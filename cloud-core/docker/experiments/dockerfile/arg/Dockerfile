# Experiment with ARG command.
#
# Build with
#  $ docker build -t test-arg .
# will create an image when running, print APP_ENVIRONMENT as dev
#
# Build with
#  $ docker build --build-arg APP_ENVIRONMENT=prod -t test-arg .
# will create an image when running, print APP_ENVIRONMENT as prod

FROM busybox

ARG APP_ENVIRONMENT
ENV APP_ENVIRONMENT ${APP_ENVIRONMENT:-dev}

ADD env.sh /

CMD ["./env.sh"]
