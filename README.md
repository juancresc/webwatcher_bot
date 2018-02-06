
## This is a telegram bot for monitorign website status and receive notifications.


## Stack

- Python (django 2.0)
- Celery / rabbitmq
- Redis
- MySQL
- Apache
- Gunicorn
- Supervisor

## Deployment

There are some config files to set up celery and gunicorn with supervisor.

    Notice: be aware and gitignore .djangopass file, I've added my own just to show how it is working
    
I've decided not to use third-party telegram frameworks or wrappers since it was so simple to just listen to the webhook calls
