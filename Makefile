# https://cloud.google.com/functions/docs/tutorials/pubsub#functions-prepare-environment-python

PROJECT=botbase
PUB_SUB_TOPIC=cron-slack-training

deploy:
	gcloud functions deploy slack_training_streak \
		--runtime=python37 \
		--trigger-topic=$(PUB_SUB_TOPIC) \
		--project=$(PROJECT) \
		--set-env-vars SLACK_BOT_TOKEN=$(SLACK_BOT_TOKEN),CHANNEL=$(CHANNEL)

pub:
	gcloud pubsub topics publish $(PUB_SUB_TOPIC) --message YES --project=$(PROJECT)