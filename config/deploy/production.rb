# server-based syntax
# ======================
# Defines a single server with a list of roles and multiple properties.
# You can define all roles on a single server, or split them:

# server 'example.com', user: 'deploy', roles: %w{app db web}, my_property: :my_value
# server 'example.com', user: 'deploy', roles: %w{app web}, other_property: :other_value
# server 'db.example.com', user: 'deploy', roles: %w{db}
server '35.156.7.51', user: 'deployer', roles: %w{app db web}
set :branch, 'master'
set :pip_requirements, 'requirements/production.txt'
set :django_settings_dir, 'Ideconference'
#set :django_settings, 'production'
#set :django_settings, 'Ideconference.settings'
set :shared_virtualenv, true
set :wsgi_file, 'Ideconference/wsgi.py'


# role-based syntax
# ==================

# Defines a role with one or multiple servers. The primary server in each
# group is considered to be the first unless any  hosts have the primary
# property set. Specify the username and a domain or IP for the server.
# Don't use `:all`, it's a meta role.

# role :app, %w{deploy@example.com}, my_property: :my_value
# role :web, %w{user1@primary.com user2@additional.com}, other_property: :other_value
# role :db,  %w{deploy@example.com}



# Configuration
# =============
# You can set any configuration variable like in config/deploy.rb
# These variables are then only loaded and set in this stage.
# For available Capistrano configuration variables see the documentation page.
# http://capistranorb.com/documentation/getting-started/configuration/
# Feel free to add new variables to customise your setup.



# Custom SSH Options
# ==================
# You may pass any option but keep in mind that net/ssh understands a
# limited set of options, consult the Net::SSH documentation.
# http://net-ssh.github.io/net-ssh/classes/Net/SSH.html#method-c-start
#
# Global options
# --------------
#  set :ssh_options, {
#    keys: %w(/home/rlisowski/.ssh/id_rsa),
#    forward_agent: false,
#    auth_methods: %w(password)
#  }
#
# The server-based syntax can be used to override options:
# ------------------------------------
# server 'example.com',
#   user: 'user_name',
#   roles: %w{web app},
#   ssh_options: {
#     user: 'user_name', # overrides user setting above
#     keys: %w(/home/user_name/.ssh/id_rsa),
#     forward_agent: false,
#     auth_methods: %w(publickey password)
#     # password: 'please use keys'
#   }

#namespace :deploy do
#   desc "Copy files"
#  task :copy_files do 
#    on roles(:app) do
#      execute :rsync , "./system_files/" , release_path.join('config/')
#    end  
#  end
#
#   task :upload_files do
#      on roles(:all) do |host|
#         %w[ gunicorn.settings.py ].each do |f|
#            upload! './system_files/' + f , './shared/config/' + f
#         end
#      end
#   end
#
##  before 'deploy:check:linked_files', 'deploy:upload_files'
##  before 'deploy:symlink:shared', 'deploy:copy_files'
##  before 'deploy:check:linked_files', 'deploy:copy_files'
namespace :deploy do
  desc "stop_monit_idconference"
  task :stop_monit_idconference do
    on roles(:all) do
      execute "sudo /usr/bin/monit stop gunicorn_idconference_si"
    end
  end
  desc "start_monit_idconference"
  task :start_monit_idconference do
    on roles(:all) do
      execute "sudo /usr/bin/monit start gunicorn_idconference_si"
    end
  end
end
before 'python:create_virtualenv' , 'deploy:stop_monit_idconference'
after 'deploy:cleanup' , 'deploy:start_monit_idconference'
#end

