# The following is a script in Lua that is to be evaluated by Redis
# (it's a feature!) on lock release, given a key and an argument the script
# will call the GET command from REDIS with the given key and if it matches
# the given argument, will delete the key (release lock), do nothing otherwise.
#
# The main purpose is to guarantee that only the owner of the lock can
# release the lock, as the lock contains a UUID known only to the
# process/machine/etc. that acquired the lock. This approach avoids race
# conditions if done outside of Redis (RTT) and is the recommended way to do it
#
# https://redis.io/docs/manual/patterns/distributed-locks/
REDIS_LOCK_RELEASE_SCRIPT: str = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""
