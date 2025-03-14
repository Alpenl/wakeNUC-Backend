import redis

from global_config import redis as redis_config

# Redis连接实例 - 用于请求频率限制
# 使用db=0数据库
redis_request_limit = redis.StrictRedis(host=redis_config['host'], port=redis_config['port'],
                                        password=redis_config['password'],
                                        encoding='utf8', decode_responses=True, db=0)

# Redis连接实例 - 用于存储用户token
# 使用db=1数据库
redis_token = redis.StrictRedis(host=redis_config['host'], port=redis_config['port'], password=redis_config['password'],
                                encoding='utf8', decode_responses=True, db=1)

# Redis连接实例 - 用于存储用户会话信息
# 使用db=2数据库，不自动解码响应（用于存储二进制数据如pickle序列化的对象）
redis_session = redis.StrictRedis(host=redis_config['host'], port=redis_config['port'],
                                  password=redis_config['password'],
                                  encoding='utf8', decode_responses=False, db=2)

# Redis连接实例 - 用于API响应缓存
# 使用db=3数据库
redis_cache = redis.StrictRedis(host=redis_config['host'], port=redis_config['port'], password=redis_config['password'],
                                encoding='utf8', decode_responses=True, db=3)

# Redis连接实例 - 用于实验课程数据缓存
# 使用db=4数据库，不自动解码响应（用于存储二进制数据）
redis_experiment = redis.StrictRedis(host=redis_config['host'], port=redis_config['port'],
                                     password=redis_config['password'], encoding='utf8', decode_responses=False, db=4)
