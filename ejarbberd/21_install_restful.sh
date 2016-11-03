#!/bin/bash

install_module_from_ejabberd_contrib() {
    wget
}

install_module_from_ejabberd_contrib

echo "Restarting ejabberd after successful module installation(s)"
ejabberdctl restart
child=$!
ejabberdctl "started"
wait $child

exit 0