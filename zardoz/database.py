from tinydb import TinyDB, Query


class RollHistory:

    def __init__(self, path):
        self.db = TinyDB(path)

    def add_roll(self, guild, member, expr, result):
        self.db.insert({'guild_id': guild.id,
                        'guild_name': guild.name,
                        'member_id': member.id,
                        'member_nick': member.nick,
                        'expr': expr,
                        'result': result})

    def query_guild(self, guild):
        Rolls = Query()
        return self.db.search(Rolls.guild_id == guild.id)

