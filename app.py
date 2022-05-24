from flask import Flask,render_template,session,request, \
    copy_current_request_context
from flask_socketio import join_room,leave_room, \
    close_room,rooms

from threading import Lock
from flask import Flask,render_template,session,request
from flask_socketio import SocketIO,emit,disconnect
import MySQLdb
import json,requests

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app,async_mode=async_mode)
thread = None
thread_lock = Lock()

#start = -5
#stop = 5

url = requests.get("http://192.168.1.52/cm?cmnd=status%2010")
text = url.text

read_ser = json.loads(text)

print(read_ser["StatusSNS"]["AM2301"]["Temperature"])
print(type(read_ser))


def background_thread(args):
    count = 0
    dataCounter = 0
    dataList = []

    # TODO DB
    db = MySQLdb.connect(host="localhost",user="root",passwd="Krusovice200*",db="poitDatabase")
    dbV = dict(args).get('btn_value')

    while True:
        socketio.sleep(1)
        count += 1

        if args:
            A = dict(args).get('A')
            dbV = dict(args).get('btn_value')
        else:
            A = 1
            dbV = 'nieco'

        socketio.sleep(2)
        count += 1
        dataCounter += 1

        print(type(args))
        print(args.get("event"))
        print(type(args.get("event")['value']))
        dbV = str(args)

        print(read_ser["StatusSNS"]["AM2301"]["Temperature"])
        print(dbV)

        if args.get("event")['value'] == '1':
            dataDict = {
                "x": dataCounter,
                "y": read_ser["StatusSNS"]["AM2301"]["Temperature"]}
            dataList.append(dataDict)

            socketio.emit('my_response',
                          {'data': read_ser["StatusSNS"]["AM2301"]["Temperature"],'count': count})
        elif args.get("event")['value'] == '0':
            print("db a subor")
            dataList = []
            dataCounter = 0


@app.route('/')
def index():
    return render_template('index.html',async_mode=socketio.async_mode)


@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count',0) + 1
    session['event'] = {'value': '0'}
    emit('my_response',
         {'data': message['data'],'count': session['receive_count']})


@socketio.event
def my_broadcast_event(message):
    session['receive_count'] = session.get('receive_count',0) + 1
    emit('my_response',
         {'data': message['data'],'count': session['receive_count']},
         broadcast=True)


@socketio.event
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count',0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.event
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count',0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close_room')
def on_close_room(message):
    session['receive_count'] = session.get('receive_count',0) + 1
    emit('my_response',{'data': 'Room ' + message['room'] + ' is closing.',
                        'count': session['receive_count']},
         to=message['room'])
    close_room(message['room'])


@socketio.event
def my_room_event(message):
    session['receive_count'] = session.get('receive_count',0) + 1
    emit('my_response',
         {'data': message['data'],'count': session['receive_count']},
         to=message['room'])


@socketio.event
def click_eventStart(message):
    session["event"] = {'value': '1'}
    print(session['event'])
    print(session)


@socketio.event
def click_eventStop(message):
    session["event"] = {'value': '0'}
    print(session['event'])
    print(session)


@socketio.event
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count',0) + 1
    # for this emit we use a callback function
    # when the callback function is invoked we know that the message has been
    # received and it is safe to disconnect
    emit('my_response',
         {'data': 'Disconnected!','count': session['receive_count']},
         callback=can_disconnect)


@socketio.event
def my_ping():
    emit('my_pong')


@socketio.event
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread,
                                                    args=session._get_current_object())
    emit('my_response',{'data': 'Connected','count': 0})


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected',request.sid)


if __name__ == '__main__':
    socketio.run(app)
