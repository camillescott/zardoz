import logging

from rich.logging import RichHandler


def setup(log_file):
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s \t %(levelname)s \t %(message)s',
        #datefmt="[%X]"
    )

    logger = logging.getLogger()
    logger.addHandler(RichHandler())

    return logger


class LoggingMixin:

    def __init__(self, *args, **kwargs):
        self.log = self.get_logger()
        self.register_decos()
        
    def register_decos(self):

        @self.bot.before_invoke
        async def log_cmd_invoke(ctx):
            self.log.info(f'CMD: [{ctx.invoked_with} {ctx.message.content}] from {ctx.author}:{ctx.guild}')

    @staticmethod
    def get_logger():
        return logging.getLogger()
