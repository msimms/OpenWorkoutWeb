#!/bin/sh

sudo apt install rabbitmq-server
sudo rabbitmqctl add_user openworkout $1
sudo rabbitmqctl add_vhost openworkout_vhost
sudo rabbitmqctl set_user_tags openworkout openworkout_tag
sudo rabbitmqctl set_permissions -p openworkout_vhost openworkout ".*" ".*" ".*"
sudo rabbitmqctl delete_user guest
sudo service rabbitmq-server start
