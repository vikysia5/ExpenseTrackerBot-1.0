// src/services/userService.js
// SRP: user management only | DIP: db injected via singleton

const database = require('../core/database');
const logger = require('../core/logger');
const { DatabaseError } = require('../core/exceptions');
const { bus } = require('../observers/eventBus');
const { timer } = require('../core/decorators');

class UserService {
  constructor(db) {
    this.db = db;
    this.findOrCreate = timer(this.findOrCreate.bind(this), 'userService.findOrCreate');
  }

  async findOrCreate(telegramUser) {
    const telegramId = String(telegramUser.id);
    logger.info('UserService', 'findOrCreate', { telegramId });

    const client = this.db.client;

    try {
      // 1. Try to find existing user
      const findResult = await client
        .from('users')
        .select('*')
        .eq('telegram_id', telegramId)
        .single();

      const existing = findResult.data;

      if (existing && existing.id) {
        logger.debug('UserService', 'User found', { id: existing.id });
        return existing;
      }

      // 2. Create new user
      const newUser = {
        telegram_id: telegramId,
        name: [telegramUser.first_name, telegramUser.last_name]
          .filter(Boolean).join(' ') || 'User',
        username:      telegramUser.username || null,
        language_code: telegramUser.language_code || 'en',
        currency:      'USD',
      };

      const insertResult = await client
        .from('users')
        .insert(newUser)
        .select()
        .single();

      if (insertResult.error) {
        // Race condition: user created between find and insert — try find again
        const retry = await client.from('users').select('*').eq('telegram_id', telegramId).single();
        if (retry.data) return retry.data;
        throw new DatabaseError('insert user', insertResult.error.message);
      }

      const created = insertResult.data;
      logger.info('UserService', 'New user created', { id: created.id, name: created.name });

      // Fire event — non-blocking
      bus.emit('user:registered', { userId: created.id, name: created.name }).catch(() => {});

      return created;

    } catch (err) {
      if (err instanceof DatabaseError) throw err;
      logger.error('UserService', 'findOrCreate error', { error: err.message });
      // Graceful fallback so app still loads
      return {
        id: 'tg_' + telegramId,
        telegram_id: telegramId,
        name: telegramUser.first_name || 'User',
        username: telegramUser.username || null,
        currency: 'USD',
      };
    }
  }

  async updateCurrency(userId, currency) {
    logger.info('UserService', 'updateCurrency', { userId, currency });
    const { data, error } = await this.db.client
      .from('users')
      .update({ currency })
      .eq('id', userId)
      .select()
      .single();
    if (error) throw new DatabaseError('update currency', error.message);
    return data;
  }
}

module.exports = new UserService(database);
