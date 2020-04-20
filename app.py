from flask import Flask, request, jsonify
from cassandra.cluster import Cluster
import json
import requests
cluster = Cluster(contact_points=['172.17.0.2'],port=9042)
session = cluster.connect()
app = Flask(__name__)

@app.route('/')
def hello():
	name = request.args.get("name","World")
	return('<h1>Hello, {}!</h1>'.format(name))

@app.route('/energy', methods=['GET'])
def profile():
	rows = session.execute( """Select * From energy.providers""")
	result=[]
	for provider in rows:
		result.append({"energyprovider":provider.energyprovider,"greenelectricity":provider.greenelectricity,"greengas":provider.greengas})
	return jsonify(result)

@app.route('/energy/emissions', methods=['GET'])
def external():
	carbon_url_template ='https://api.carbonintensity.org.uk/regional/postcode/{postcode}'
	my_postcode = 'E1'
	carbon_url = carbon_url_template.format(postcode = my_postcode)
	resp = requests.get(carbon_url)
	if resp.ok:
		carbon = resp.json()
		return jsonify(resp.json())
	else:
		print(resp.reason)

@app.route('/energy', methods=['POST'])
def create():
	session.execute( """INSERT INTO energy.providers(energyprovider,greenelectricity,greengas) VALUES( '{}',{},{})""".format(request.json['energyprovider'],int(request.json['greenelectricity']), int(request.json['greengas'])))
	return jsonify({'message': 'created: /providers/{}'.format(request.json['energyprovider'])}), 201

@app.route('/energy', methods=['PUT'])
def update():
	session.execute( """UPDATE energy.providers SET greenelectricity={}, greengas={} WHERE energyprovider= '{}'""".format(int(request.json['greenelectricity']), int(request.json['greengas']), request.json['energyprovider']))
	return jsonify({'message': 'updated: /providers/{}'.format(request.json['energyprovider'])}), 200

@app.route('/energy', methods=['DELETE'])
def delete():
	session.execute( """DELETE FROM energy.providers WHERE energyprovider= '{}'""".format(request.json['energyprovider']))
	return jsonify({'message': 'deleted: /providers/{}'.format(request.json['energyprovider'])}), 200

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=80)
