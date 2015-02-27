#!/usr/bin/python
# -*- coding: UTF-8 -*-
 
import sys
import argparse
import sqlite3
import boto
import time

try:
    # Creates or opens a file called mydb with a SQLite3 DB
    db = sqlite3.connect('inst.dat')
    # Get a cursor object
    cursor = db.cursor()
except Exception as e:
        # Roll back any change if something goes wrong
        db.rollback()
        print('error database connection')

def create_table():
    print('create table')
    try:
        # Check if table users does not exist and create it
        cursor.execute('''CREATE TABLE IF NOT EXISTS instances(reservation_id TEXT PRIMARY KEY, public_dns TEXT, private_dns TEXT)''')
        # Commit the change
        db.commit()
    # Catch the exception
    except Exception as e:
        # Roll back any change if something goes wrong
        db.rollback()
        print('error table creation')

def delete_table():
    print('delete table')
    cursor.execute('''DROP TABLE instances''')
    db.commit()

def insert_rec(reserv_id, pub_dns, priv_dns):
    try:
        with db:
            db.execute('''INSERT INTO instances(reservation_id ,public_dns , private_dns) VALUES(?,?,?)''', (reserv_id, pub_dns, priv_dns))
    except sqlite3.IntegrityError:
        print('Record already exists')

def select_by_id(reserv_id):
    print('request to db')
    cursor.execute('''SELECT * FROM instances WHERE reservation_id = ? ''', (reserv_id))
    for row in cursor:
        print(row)

def delete_rec_by_id(reserv_id):
    print('delete record from db')
    try:
        #delete_rec_id = input('record id:')
        cursor.execute('''DELETE FROM instances WHERE reservation_id = ? ''', (reserv_id,))
        db.commit()
    except Exception as e:
        # Roll back any change if something goes wrong
        #db.rollback()
        print('error deleting')

def select_all_from_table():
    print('get all info from table')
    cursor.execute('''SELECT * FROM instances''')
    for row in cursor:
        print(row)

def boto_connect(access_key,secret_key):
    ec2 = boto.connect_ec2(aws_access_key_id=access_key,
                                  aws_secret_access_key=secret_key)
    return ec2
 
 
def createParser ():
    parser = argparse.ArgumentParser()
    parser.add_argument ('-r', '--run', '--run_instance', nargs=1)
    parser.add_argument ('-ak','--aws_access_key')
    parser.add_argument ('-sk','--aws_secret_access_key')
    parser.add_argument ('-a', '--ami')
    parser.add_argument ('-kn', '--key_name')
    parser.add_argument ('-it', '--instance_type')
    parser.add_argument ('-s', '--stop', '--stop_instance')
    parser.add_argument ('-t', '--terminate', '--terminate_instance')
    parser.add_argument ('-dbi', '--db_info')
    parser.add_argument ('-ii', '--instances_info')
    return parser

#check keys for connecting to amazon
def check_keys():
    if namespace.aws_access_key and namespace.aws_secret_access_key:
        print ("aws_access_key, {}".format (namespace.aws_access_key) )
        print ("aws_secret_access_key: ", namespace.aws_secret_access_key)
        aws_keys = 1
    else:
        print ("aws_access_key or(and) aws_secret_access_key absent")
        aws_keys = 0

    return aws_keys

# check running parameters present: 'ami','key_name','instance_type'
def check_running_param():
    if namespace.ami and namespace.key_name and namespace.instance_type:
        print("ami: ", namespace.ami)
        print("key_name: ", namespace.key_name)
        print("instance_type", namespace.instance_type)
        param = 1
    else:
        print ("wrong running parameters (one of 'ami','key_name','instance_type') ")
        param = 0
    return param

 
if __name__ == '__main__':
    parser = createParser()
    namespace = parser.parse_args(sys.argv[1:])

    print (namespace)

# Create table if not exist
create_table()
    
# run instance & write to db    
if namespace.run:
    print ("run, {}".format (namespace.run[0]) )
    if check_keys() and check_running_param():
        #print ("try connect to ec2")
        connection = boto_connect(namespace.aws_access_key, namespace.aws_secret_access_key)
        try:
            reservation = connection.run_instances(namespace.ami, key_name=namespace.key_name ,instance_type=namespace.instance_type)
            print ("instance  with reservation id = ", reservation.id, " starting, wait a minute...")
            
            print ("Waiting for AWS to start instance(s)...")
            res_id = reservation.instances[0].id
            print ("instance id = ", res_id)
            while reservation.instances[0].state != u'running':
                time.sleep(10)
                print(int(time.clock()), " state: ", reservation.instances[0].state)
                reservation = connection.get_all_instances([res_id])[0]
            print(int(time.clock()), " state: ", reservation.instances[0].state)
            # and now write res_id to db...
            insert_rec(reservation.id, reservation.instances[0].public_dns_name, reservation.instances[0].private_dns_name)
            print ("write to db: reservation = ", reservation.id, " public_dns = ", reservation.instances[0].public_dns_name,
                   "priv_dns = ", reservation.instances[0].private_dns_name)
            

        except EC2ResponseError as exception:
            print ("An error occurred please check parameters! \n")

    '''raw = input('Press enter to stop instance')
    reservation.instances[0].terminate()'''

# stop instance
elif namespace.stop:
    print("try stopped instance")
    reservation = namespace.stop
    print("try stopping instance ", reservation)
    #reservation.instances[0].stop
    
# terminate instance and delete from db
elif namespace.terminate:
    if check_keys():
        #print ("try connect to ec2")
        connection = boto_connect(namespace.aws_access_key, namespace.aws_secret_access_key)
    reservation_id = namespace.terminate
    print("try terminate instance.. ", reservation_id)
    for r in connection.get_all_instances():   
        if r.id == reservation_id:
            r.instances[0].terminate()
            print(r.id,'terminated')
            delete_rec_by_id(reservation_id)
            print("ok")

    
# get all instances_info
elif namespace.instances_info:
    print('instances info')
    if check_keys():
        connection = boto_connect(namespace.aws_access_key, namespace.aws_secret_access_key)
        for r in connection.get_all_instances():
            print ('reservation.id : ',r.id)
            print ('instance_type  : ',r.instances[0].instance_type)
            print ('instance.state : ',r.instances[0].state)
            print ('public_dns_name: ',r.instances[0].public_dns_name)  
            print ('private_dns    : ',r.instances[0].private_dns_name)
            print ('SSH key associated with the instance: ',r.instances[0].key_name)

# get all info about instances from db
elif namespace.db_info:
    select_all_from_table()

        

db.close()
