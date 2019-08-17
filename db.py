import os
import psycopg2
import urllib
import logging

urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

logger = logging.getLogger(__name__)

def connect():
    return psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )

conn = connect()
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS doodles (id serial primary key, chat_id integer, message_id integer, options text)')
c.execute('CREATE TABLE IF NOT EXISTS answers (doodle_id integer not null, user_id integer not null, option text, answer text, user_name text, primary key(doodle_id, user_id, option))')
conn.close()

def create_doodle(chat_id, message_id, options):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO doodles (chat_id, message_id, options) VALUES (%s, %s, %s) RETURNING id", [chat_id, message_id, options])
    doodle_id = c.fetchone()[0]
    conn.commit()
    conn.close()
    return doodle_id

def get_doodle(chat_id, message_id):
    conn = connect()
    c = conn.cursor()

    logger.info("get doodle for chat_id: %s message_id: %s" % (chat_id, message_id))

    c.execute("SELECT id, options FROM doodles WHERE chat_id=%s AND message_id=%s", [chat_id, message_id])
    row = c.fetchone()
    doodle_id = row[0]
    options = row[1].split(",")


    c.execute("SELECT user_name, option, answer FROM answers WHERE doodle_id=%s", [doodle_id])

    doodle = {}
    for row in c.fetchall():
        user_name = row[0]
        option = row[1]
        answer = row[2]
        if user_name in doodle:
            user = doodle[user_name]
        else:
            user = {}
            doodle[user_name] = user

        user[option] = answer

    conn.commit()
    conn.close()
    return {
        'id': doodle_id,
        'options': options,
        'answers': doodle
    }


def get_answer(doodle_id, user_id, option):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT answer FROM answers WHERE doodle_id = %s AND user_id = %s AND option = %s", [doodle_id, user_id, option])
    answer_row = c.fetchone()
    if answer_row:
        answer = answer_row[0]
    else:
        answer = None

    conn.commit()
    conn.close()
    return answer

def set_answer(doodle_id, user_id, user_name, option, answer):
    conn = connect()
    c = conn.cursor()

    existing = get_answer(doodle_id, user_id, option)
    if not existing:
        logger.info("insert")
        c.execute("INSERT INTO answers (doodle_id, user_id, option, answer, user_name) VALUES (%s, %s, %s, %s, %s)", [doodle_id, user_id, option, answer, user_name])
    else:
        logger.info("update")
        c.execute("UPDATE answers SET answer = %s WHERE doodle_id = %s AND user_id = %s AND option = %s ", [answer, doodle_id, user_id, option])

    conn.commit()
    conn.close()
