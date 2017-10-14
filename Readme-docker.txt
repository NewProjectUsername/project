= Docker =

Docker is the world’s leading software container platform.
Containers are a way to package software in a format that can run isolated on a
shared operating system. Unlike VMs, containers do not bundle a full operating
system - only libraries and settings required to make the software work are
needed. This makes for efficient, lightweight, self-contained systems and
guarantees that software will always run the same, regardless of where it’s
deployed.

See also: https://docs.docker.com/get-started/
see also: https://docs.docker.com/compose/

= Development environment =
== Requirements ==
* Docker
* Docker compose

== Usage ==

To run development version of application just run `docker-compose up` in project
root directory. This will build docker image described in Dockerfile and then
start environment (database and web server) described in docker-compose.yml file.
First it will start db server and expose db port on host machine (This enables
us to connect to database just if it was installed locally on host machine).
Once db server is up and running docker composer will start web server, execute
migrations and run application server.
Connect to db and create user:
`INSERT INTO conference.Landing_user VALUES (0, "pbkdf2_sha256$30000$V5YXdIw7ir8Y$FcUbcRMASQssjJsFbjp9b6gVrakJXt38QshR8/MN4O8=", NULL, 1, "Enver", "Cicak", "enver.cicak@gmail.com", 0, 1, "2017-09-30 06:03:38.948135", "enver");
INSERT INTO conference.Visitor_profile values(0, 'M', 1982, "Naselje Luke", "Visoko", "71300", NULL, "+38761455215", 1);`
Open browser and go to http://localhost:8000
Login as username: enver.cicak@gmail.com, password: enver001

== Destroy environment ==
Run `docker-compose down` to destroy running containers.
Run `docker rmi ideconference_web` to destroy web server image.

= Deployment options =
Application can be deployed to staging/production as a Docker container with
minor adjustments. Instead of mounting application code in docker-compose (used
to sync development changes automatically) we need to copy code to docker image
and copy it to server to be deployed on staging/production.

Also application can be deployed in a traditional way by installing db server
and connecting web application to it.
