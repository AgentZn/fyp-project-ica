
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

cloud_config= {
  'secure_connect_bundle': 'C:\secure-connect-fyp-ica.zip'
}
auth_provider = PlainTextAuthProvider('RxnkOimyTprpDRaWZyEfWZTz', '5ydlP0.DQvbKjBv-GTt7tWxQnpBk5A+Kg84d3MZojxSNo8wciB+i0RnzYL_MIQgKgpCZEp9PH5Cdhf,s-1mJdEweY9N2vClPu+EqSlfmG1vHuAuw,9eS7k.UzrDOwT8W')
cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
session = cluster.connect()

row = session.execute("select release_version from system.local").one()
if row:
  print(row[0])
else:
  print("An error occurred.")