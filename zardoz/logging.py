import logging

from rich.logging import RichHandler


# Set up rich logging handler
# (discord.py uses the python logger)
logging.basicConfig(
    level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)


class LoggingMixin:

    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger('discord')
        self.register_decos()
        
    def register_decos(self):

        @self.bot.before_invoke
        async def log_cmd_invoke(ctx):
            self.log.info(f'CMD: [{ctx.invoked_with} {ctx.message.content}] from {ctx.author}:{ctx.guild}')
