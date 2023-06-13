import sys


def main(*args, **kwargs):
  from threemystic_cloud_data_client.cli import cloud_data_client_cli
  cloud_data_client_cli().main(*args, **kwargs)
  

if __name__ == '__main__':   
  main(sys.argv[1:])