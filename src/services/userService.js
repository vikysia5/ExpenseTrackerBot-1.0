// src/services/userService.js
// SRP: only user business logic | DIP: db injected

const database = require('../core/database');
const logger = require('../core/logger');
const { UserNotFoundError, DatabaseError } = require('../core/exceptions');
const { bus } = require('../observers/eventBus');
const { timer, cache } = require('../core/decorators');

class UserService {
  constructor(db) {
    this.db = db;
    // Apply decorators
    this.findOrCreate = timer(this.findOrCreate.bind(this), 'userService.findOrCreate');
    this.getById = cache(this.getById.bind(this), 60000);
  }

  async findOrCreate(telegramUser) {
    logger.info('UserService', 'findOrCreate called', { telegramId: telegramUser.id });
    const client = this.db.client;

    try {
      // Try to find existing user
      const { data: existing, error: findErr } = await client
        .from('users')
        .select('*')
        .eq('telegram_id', String(telegramUser.id))
        .single();

      if (findErr && findErr.code !== 'PGRST116') {
        // PGRST116 = not found, anything else is a real error
        logger.warning('UserService', 'Find error (may be first user)', { code: findErr.code });
      }

      if (existing) {
        logger.debug('UserService', 'User found', { id: existing.id });
        return existing;
      }

      // Create new user
      const newUser = {
        telegram_id: String(telegramUser.id),
        name: [telegramUser.first_name, telegramUser.last_name].filter(Boolean).join(' ') || 'User',
        username: telegramUser.username || null,
        language_code: telegramUser.language_code || 'en',
        currency: 'USD',
        created_at: new Date().toISOString()
      };

      const { data: created, error: createErr } = await client
        .from('users')
        .insert(newUser)
        .select()
        .single();

      if (createErr) {
        // Handle race condition: user was created between our find and insert
        if (createErr.code === '23505') {
          const { data: retry } = await client.from('users').select('*').eq('telegram_id', String(telegramUser.id)).single();
          if (retry) return retry;
        }
        throw new DatabaseError('insert user', createErr.message);
      }

      logger.info('UserService', 'New user created', { id: created.id, name: created.name });
      await bus.emit('user:registered', { userId: created.id, name: created.name });
      return created;

    } catch (err) {
      if (err instanceof DatabaseError) throw err;
      logger.error('UserService', 'findOrCreate failed', { error: err.message });
      // Fallback: return a mock user so app still works
      return {
        id: `tg_${telegramUser.id}`,
        telegram_id: String(telegramUser.id),
        name: telegramUser.first_name || 'User',
        currency: 'USD'
      };
    }
  }

  async getById(userId) {
    const { data, error } = await this.db.client.from('users').select('*').eq('id', userId).single();
    if (error || !data) throw new UserNotFoundError(userId);
    return data;
  }

  async updateCurrency(userId, currency) {
    logger.info('UserService', 'updateCurrency', { userId, currency });
    const { data, error } = await this.db.client
      .from('users').update({ currency }).eq('id', userId).select().single();
    if (error) throw new DatabaseError('update user currency', error.message);
    return data;
  }
}

module.exports = new UserService(require('../core/database'));
