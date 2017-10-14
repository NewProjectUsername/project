# config valid only for current version of Capistrano
lock '3.6.1'

#set :application, 'my_app_name'
set :application, 'cardapp1'
#set :repo_url, 'git@example.com:me/my_repo.git'
set :repo_url, 'git@bitbucket_idconference:identiks_team/ideconference.git'

set :stages, %w(staging production)
set :default_stage, 'staging'

# Default branch is :master
# ask :branch, `git rev-parse --abbrev-ref HEAD`.chomp

# Default deploy_to directory is /var/www/my_app_name
# set :deploy_to, '/var/www/my_app_name'
set :deploy_to, '/home/deployer/apps/cardapp1/webdir/'

# Default value for :scm is :git
# set :scm, :git

# Default value for :format is :airbrussh.
# set :format, :airbrussh

# You can configure the Airbrussh format using :format_options.
# These are the defaults.
# set :format_options, command_output: true, log_file: 'log/capistrano.log', color: :auto, truncate: :auto

# Default value for :pty is false
# set :pty, true

# Default value for :linked_files is []
# append :linked_files, 'config/database.yml', 'config/secrets.yml'
#append :linked_files, 'db/db.sqlite3'

# Default value for linked_dirs is []
# append :linked_dirs, 'log', 'tmp/pids', 'tmp/cache', 'tmp/sockets', 'public/system'
append :linked_dirs, 'log' , 'pids' , 'config' , 'static' , 'wsgi' , 'db'

# Default value for default_env is {}
# set :default_env, { path: "/opt/ruby/bin:$PATH" }

# Default value for keep_releases is 5
# set :keep_releases, 5

#namespace :deploy do
#  desc "Restart gunicorn"
#  task :restart_gunicorn do
#    on roles(:app) do
#      execute 'sudo /usr/bin/monit restart gunicorn_idekonferenca_si'
#    end
#  end
#
#  after :finishing, :restart_gunicorn
#end

