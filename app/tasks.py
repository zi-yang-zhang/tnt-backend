import logging

from factory import create_celery_app

celery = create_celery_app()


@celery.task
def debug_log(msg):
    logging.getLogger().debug(msg)
