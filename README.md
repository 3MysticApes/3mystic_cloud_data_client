# 3mystic_cloud_data_client
A set of scripts to help uniformly pull data from the cloud providers for various resources.
Currently supports AWS/Azure

# Install

## pip

This project is currently designed to be installed via pip
Currently the project is under development and is not in PyPI. 
So you need to install the following packages <br/>
pip install https://github.com/3MysticApes/3mystic_common <br/>
pip install https://github.com/3MysticApes/3mystic_cloud_client <br/>
pip install https://github.com/3MysticApes/3mystic_cloud_data_client <br/>

Once installed you will get the following command:
3mystic_cloud_data_client

The above command allows you to configure the cloud client.

# Contribute

This project is packaged using Hatch. If you need to install Hatch please refer to their documentation
https://hatch.pypa.io/latest/install/


You should be able to run the following command in the root directory for a general status
hatch status

Then from the root directory you can run
pip install ./

I would suggest while you are debugging issues to install it with the command below. Once you are done with your development you can uninstall. This allows you to make edits and test easier.
pip install -e ./
https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-e