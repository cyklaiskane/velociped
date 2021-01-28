DOCKER_IMAGES := mapproxy tileserver varnish

.PHONY: prod deploy run logs push images $(DOCKER_IMAGES)

prod:
	docker build --build-arg BUILD_ENV=prod -t velociped -t trivectortraffic/velociped .

dev:
	docker build --build-arg BUILD_ENV=dev -t velociped:dev -t trivectortraffic/velociped:dev .

run:
	docker-compose -f docker-compose-common.yml -f docker-compose-dev.yml up --remove-orphans -d db cyklaiskane-app
	sleep 5
	docker-compose -f docker-compose-common.yml -f docker-compose-dev.yml up -d tileserver

logs:
	docker-compose -f docker-compose-common.yml -f docker-compose-dev.yml logs -ft --tail=10

deploy:
	./deploy.sh

push:
	docker push trivectortraffic/velociped

images: $(DOCKER_IMAGES)

$(DOCKER_IMAGES):
	docker build -t cyklaiskane-$@ $@
