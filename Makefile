.PHONY: prod deploy run

prod:
	docker build -t velociped .

run:
	docker run -it --rm -e POSTGRES_DSN='postgres://velociped:foobar@db/velociped' --network=velociped_default -p 8008:8000 velociped

velociped.tar: prod
	docker image save -o velociped.tar velociped

deploy: velociped.tar .env docker-compose-deploy.yml
	rsync -avhP velociped.tar .env docker-compose-deploy.yml debian@docker-host-02:velociped/
	ssh debian@docker-host-02 "docker image load -i velociped/velociped.tar; cd velociped; docker-compose -f docker-compose-deploy.yml up -d"
