DOCKER_IMAGES := mapproxy tileserver varnish

.PHONY: all prod dev images $(DOCKER_IMAGES)

all: prod images

prod:
	docker build --build-arg BUILD_ENV=prod -t velociped -t trivectortraffic/velociped .

dev:
	docker build --build-arg BUILD_ENV=dev -t velociped:dev -t trivectortraffic/velociped:dev .

images: $(DOCKER_IMAGES)

$(DOCKER_IMAGES):
	docker build -t cyklaiskane-$@ $@
