.PHONY: prod deploy run logs push

prod:
	docker build -t velociped -t trivectortraffic/velociped .

run:
	docker-compose -f docker-compose.yml -f docker-compose-dev.yml up --remove-orphans -d db cyklaiskane-app
	sleep 5
	docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d tileserver

logs:
	docker-compose -f docker-compose.yml -f docker-compose-dev.yml logs -ft --tail=10

deploy:
	./deploy.sh

push:
	docker push trivectortraffic/velociped
