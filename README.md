#IDConference

## Timezones

I'm putting this on top because it's kinda important and new.

Every time the times and dates are shown for an event, they must be converted to the timezone of the particular event. This ensures, that
the time will be displayed the same as in the city where the event will eventually take place.

Lets take an example, by printing out a starting date and time for an event entry in a template:
```
{{ event.start_time|timezone:event.timezone }}
```

and thats it. For sorting which event are yet to happen and which happen before or after, UTC can be used which how the dates and times are
stored in the database.

## Server and login

ubuntu@52.57.93.164
- user ubuntu (root rights)
- user deployer (deploy rights)

HOW-TO : ssh to server using forward agent " ssh -A <USER>@35.156.7.53 "

Ask Klemen or Tomaž to add your public key to server.

## Deploy

User deployer can deploy.

Go to home folder of deployer user ( /home/deployer/ )

Here all apps should have their repos downloaded.
Example for deploying mala_ulica repo :

```
cd /home/deployer/repos_capistrano/mu_prod
run: ./deploy-staging.sh
run: ./deploy-production.sh
```

## Requirements

Requirements are auto installed at each deploy, please fill requirements in requiremens/<STAGE>.txt
```
install html to pdf library
* linux: sudo apt-get install wkhtmltopdf 
* server without X11: https://gist.github.com/k4v3h/6de0d0d564e54856930d4af7214a37a2
* windows: (?) https://wkhtmltopdf.org/downloads.html

```


## Manually adding static files

Static files that you want to add to your project manually should go to static_manual folder in the repo.

## Static files

Are in static folder.

## Database (db.sqlite3 )

Database is shared between releases so it shouldn't be in the repo.
The app expects database in db/db.sqlite3 (and it's symlinked at deploy process)

