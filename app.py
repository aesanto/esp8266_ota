from flask import Flask, request, send_from_directory, render_template, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os


app = Flask(__name__)
app.secret_key = 'aesanto'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///esp8266.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['UPLOAD_FOLDER']='static/bin'
db = SQLAlchemy(app)

class Sensores(db.Model):
	id=db.Column('id', db.Integer, primary_key=True)
	nome=db.Column('nome', db.String)
	descricao=db.Column('descricao',db.String)
	versao=db.Column('versao', db.String)
	mac=db.Column('mac', db.String)
	filename=db.Column('filename',db.String)
	def __init__(self, nome, descricao, versao, mac, filename):
		self.nome = nome
		self.descricao = descricao
		self.versao = versao
		self.mac = mac
		self.filename = filename


@app.route('/')
def index():
	sensores=Sensores.query.all()
	return render_template('index.html',sensores=sensores)

@app.route('/new', methods=['GET', 'POST'])
def new():
	if request.method=='GET':
		return render_template('new.html')
	if request.method=='POST':
		if request.files['file'].filename == '':
			flash('Ficheiro não selecionado')
			return render_template('new.html')
		file=request.files['file']
		f=file.filename
		#Valida se já existe um MAC
		MAC=request.form.get('MAC')
		if Sensores.query.filter_by(mac=MAC).first() is not None:
			flash("Endereço MAC existente")
			return render_template('new.html') 
		#Grava ficheiro
		print(f)
		if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER']+'/'+MAC)):
			os.makedirs(os.path.join(app.config['UPLOAD_FOLDER']+'/'+MAC))
		file.save(os.path.join(app.config['UPLOAD_FOLDER']+'/'+MAC, f))
		novo=Sensores(nome=request.form.get('nome'),
			descricao=request.form.get('descricao'),
			versao=request.form.get('versao'),
			mac=request.form.get('MAC'),
			filename=f)
		db.session.add(novo)
		db.session.commit()
		return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
	if request.method=='GET':
		sensor=Sensores.query.filter_by(id=id).first()
		if sensor is None:
			flash('O sensor não existe')
			return render_template('edit.html')
		return render_template('edit.html',sensor=sensor)
	if request.method=='POST':
		sensor=Sensores.query.filter_by(id=id).first()
		file=request.files['file']
		f=file.filename
		MAC=request.form.get('MAC')
		file.save(os.path.join(app.config['UPLOAD_FOLDER']+'/'+MAC, f))
		sensor.descricao=request.form.get('descricao')
		sensor.versao=request.form.get('versao')
		sensor.filename=f
		db.session.commit()
		return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete(id):
	sensor=Sensores.query.filter_by(id=id).first()
	db.session.delete(sensor)
	db.session.commit()
	return redirect(url_for('index'))


@app.route('/update')
def update():
	print('Hello')
	if request.headers.get('X-Esp8266-Version'):
		h_versao=request.headers.get('X-Esp8266-Version')
		nome=h_versao.split('-')[0]
		versao=h_versao.split('-')[1]
		mac=request.headers.get('X-Esp8266-Sta-Mac')
		sensor=Sensores.query.filter_by(mac=mac).first()
		if sensor is None:
			return "Sensor nao encontrado",500
		if versao==sensor.versao:
			return "Nao modificado",304
		file='bin/'+sensor.mac+'/'+sensor.filename
		return app.send_static_file(file)
	else:
		return 'Error'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
