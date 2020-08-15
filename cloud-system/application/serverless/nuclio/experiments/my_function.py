import os

def my_entry_point(context, event):
  # use the logger, outputting the event body
  context.logger.info_with(
    'Got invoked',
    trigger_kind=event.trigger.kind,
    event_body=event.body,
    some_env=os.environ.get('MY_ENV_VALUE'))

  # check if the event came from cron
  if event.trigger.kind == 'cron':
    # log something
    context.logger.info('Invoked from cron')
  else:
    # return a response
    return 'A string response'
