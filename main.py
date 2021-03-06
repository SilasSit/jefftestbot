import time
import random
import datetime
import pytz
import pymysql
import urllib
import requests
import json
import langcodes
from html.parser import HTMLParser
from config import *
import corgi
import trans
from telegraph import telegraph
import id
import re
import wwstats

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, BaseFilter, CallbackQueryHandler, Job, RegexHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging
from mwt import MWT

db2 = None
cursor = None

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

MWT(timeout=60*60)

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def achv(bot, update):
    add(update.message)
    from_id = update.message.from_user.id
    try:
        msg, msg2 = wwstats.check(from_id)
        bot.sendMessage(chat_id = from_id, text = msg, parse_mode='Markdown')
        bot.sendMessage(chat_id = from_id, text = msg2, parse_mode='Markdown')
        if update.message.chat.type != 'private':
            update.message.reply_text("I sent you your achivements in private.")
    except:
        keyboard = [[InlineKeyboardButton("Start Me!", url="telegram.me/"+BOT_USERNAME)]]
        markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Please click 'Start Me' to receive my message!", reply_markup=markup)


def dict(bot, update, args):
    chat_id = update.message.chat.id
    msgid = update.message.message_id
    from_id = update.message.from_user.id
    reply_to = update.message.reply_to_message

    add(update.message)
    bye = checkbanned(from_id)
    if bye == 1:
        return

    if not args:
        bot.sendMessage(chat_id, "Use `/dict <word>`", reply_to_message_id=msgid, parse_mode='Markdown')
        return
    else:
        if len(args) > 1:
            bot.sendMessage(chat_id, "Use `/dict <word>`", reply_to_message_id=msgid, parse_mode='Markdown')
            return
        word = args[0]
        result = dict_go(word)
        bot.sendMessage(chat_id, result, reply_to_message_id=msgid, parse_mode='Markdown')

def dict_go(word):
    url = "https://od-api.oxforddictionaries.com/api/v1/entries/en/" + word.lower() + "/definitions"
    randnum = random.randint(0,1)
    if randnum == 0:
        apikey = OXFORD_API_1
    else:
        apikey = OXFORD_API_2
    appid = OXFORD_ID
    try:
        r = requests.get(url, headers = {'app_id': appid, 'app_key': apikey})
        result = r.json()
        list = result['results'][0]['lexicalEntries']
        msg = "Definition(s) of word `%s`:\n" % word
        num = 1
        for each in list:
            msg += str(num) + ": `" + str(each['entries'][0]['senses'][0]['definitions'][0])[:-1] + "`\n"
            num = num + 1
        return msg
    except:
        msg = "Sorry, I cannot find the definitions of word `%s`." % word
        return msg

def ud(bot, update, args):
    chat_id = update.message.chat.id
    msgid = update.message.message_id
    from_id = update.message.from_user.id
    reply_to = update.message.reply_to_message

    add(update.message)
    bye = checkbanned(from_id)
    if bye == 1:
        return

    if not args:
        bot.sendMessage(chat_id, "Use `/ud <something here>`", reply_to_message_id=msgid, parse_mode='Markdown')
        return
    else:
        word = " ".join(args)
        result = ud_go(word)
        bot.sendMessage(chat_id, result, reply_to_message_id=msgid, parse_mode='Markdown')

def ud_go(word):
    url = "https://mashape-community-urban-dictionary.p.mashape.com/define?term=" + urllib.parse.quote(word.lower(), safe='')
    apikey = UD_API
    try:
        r = requests.get(url, headers = {"X-Mashape-Key": UD_API, "Accept": "text/plain"})
        result = r.json()
        if result['result_type'] == 'no_results':
            msg = "Sorry. No results for `%s`." % word
            return msg
        list = result['list']
        msg = "Query of `%s` on Urban Dictionary:\n" % word
        num = 1
        limit = 1
        for each in list:
            msg += str(num) + ": `" + str(each['definition']) + "`\n"
            break
        return msg
    except:
        msg = "Sorry, I found nothing about `%s` on Urban Dictionary." % word
        return msg


def showinfo(bot, update):
    msg = id.showinfo(update.message)
    update.message.reply_text(msg, parse_mode='Markdown')

def tg(bot, update):
    if update.message.reply_to_message is not None:
        url = telegraph(update.message.reply_to_message)
        update.message.reply_text(url)
    else:
        update.message.reply_text("reply to a message")

def repeat(bot, update, args):
    if len(args) == 0:
        return
    else:
        bot.sendChatAction(update.message.chat.id, action='typing')
        msg = " ".join(args)
#        escape_chars = '\*_`\['
#        msg = re.sub(r'([%s])' % escape_chars, r'\\\1', msg)
        time.sleep(3)
        update.message.reply_text(msg, parse_mode='Markdown')

def get_admin_ids(bot, chat_id):
    return [admin.user.id for admin in bot.getChatAdministrators(chat_id)]

def corgii(bot, update):
    chat_id = update.message.chat.id
    msgid = update.message.message_id
    add(update.message)
    bot.sendChatAction(chat_id, action="upload_photo")
    link = corgi.corgi()
    bot.sendPhoto(chat_id, photo=link, caption="BUTTIFUL!", reply_to_message_id = msgid)

def add(msg):
    chat_type = msg.chat.type
    chat_id = msg.chat.id
    msgid = msg.message_id
    from_id = msg.from_user.id
    reply_to = msg.reply_to_message
    from_user_name = msg.from_user.first_name
#    from_user_e = db2.escape_string(from_user_name)
    from_username = msg.from_user.username
    if msg.from_user.last_name is not '':
        from_user_name += " " + msg.from_user.last_name
    from_user_e = db2.escape_string(from_user_name)
    
    try:
        if chat_type == 'group' or chat_type == 'supergroup':
            group_id = chat_id
            group_name = db2.escape_string(msg.chat.title)
            checkgroupexist = "select * from `group` where groupid=%d" % group_id
            groupcount = cursor.execute(checkgroupexist)
            if groupcount == 0:
                newgroup = 1
                addgroup = "insert into `group` (`name`, `groupid`) values ('%s', %d)" % (group_name, group_id)
                cursor.execute(addgroup)
                db2.commit()
            else:
                newgroup = 0
                updategroup = "update `group` set name='%s' where groupid=%d" % (group_name, group_id)
                cursor.execute(updategroup)
                db2.commit()
    except:
        print("Add/Update Group error")
    try:
        adduser = "insert into user (`name`, `telegramid`, `username`) values ('%s', %d, '%s')" % (from_user_e, from_id, from_username)
        cursor.execute(adduser)
        db2.commit()
    except:
        updateuser = "update user set name='%s', username='%s' where telegramid=%d" % (from_user_e, from_username, from_id)
        cursor.execute(updateuser)
        db2.commit()

    if reply_to is not None:
        to_user = reply_to.from_user
        to_user_name = to_user.first_name
        if to_user.last_name is not '':
            to_user_name += " " + to_user.last_name
        to_user_name_e = db2.escape_string(to_user_name)
        to_user_id = to_user.id
        to_user_username = to_user.username
        try:
            addreplyuser = "insert into user (name, username, telegramid) values ('%s', '%s', %d)" % (to_user_name_e, to_user_username, to_user_id)
            cursor.execute(addreplyuser)
            db2.commit()
        except:
            editreplyuser = "update user set name='%s', username='%s' where telegramid=%d" % (to_user_name_e, to_user_username, to_user_id)
            cursor.execute(editreplyuser)
            db2.commit()

def money(bot, update, groupdict):
    amount = str(groupdict['amount']).replace(",", "")
    a = groupdict['a'].upper()
    b = groupdict['b'].upper()
    url = "http://api.fixer.io/latest"
    url += "?base=" + a + "&symbols=" + b
    response = requests.get(url)
    result = response.json()
    rate = result['rates'][b]
    after = "%.3f" % (float(amount)*rate)
    msg = "`" + amount + " " + a + "` = `" + str(after) + b + "`"
    update.message.reply_text(msg, parse_mode='Markdown')

def t(text):
    a = trans.trans(text)
    original_langcode = a[0]
    x = langcodes.Language.get(original_langcode)
    lang = x.language_name()
    if x.region_name() != None:
        lang += " (" + x.region_name() + ")"
    if x.script_name() != None:
        lang += " - " + x.script_name()
    translated = a[1]
    output = "Translated from: %s\n" % lang
    output += "`%s`" % translated

    return output

def translatee(bot, update, args):
    chat_id = update.message.chat.id
    msgid = update.message.message_id
    from_id = update.message.from_user.id
    reply_to = update.message.reply_to_message
    
    add(update.message)
    bye = checkbanned(from_id)
    if bye == 1:
        return
        
    if not args:
        if reply_to is not None:
            tr = t(reply_to.text)
            bot.sendMessage(chat_id, tr, parse_mode='Markdown', reply_to_message_id=msgid)
        else:
            bot.sendMessage(chat_id, "Reply to a message to translate, or use `/t <something here>`", reply_to_message_id=msgid, parse_mode='Markdown')
    else:
        before = " ".join(args)
        after = t(before)
        bot.sendMessage(chat_id, after, reply_to_message_id=msgid, parse_mode='Markdown')

#def google(commandonly, querytype, querytext, chat_id, msgid):
#    querytype = update.message.chat
#    if commandonly == 1:
#         bot.sendMessage(chat_id, "Please use `!gg <QUERY>` to search.", reply_to_message_id=reply_to, parse_mode='Markdown')
#         return
#    url = "https://www.googleapis.com/customsearch/v1?"
#    apikey = GOOGLE_API
#    cseid = CSE_ID
#    url += "key=" + apikey
#    url += "&cx=" +  CSE_ID
#    url += "&q=" + urllib.parse.quote(querytext)
#    if querytype == 'text':
#        print("Searching text")
#    elif querytype == 'image':
#        print("Searching image")
#        url += "&searchType=image"
#    print(url)
#    response = requests.get(url)
#    result = response.json()
#    s_title = result['items'][0]['title']
#    s_link = result['items'][0]['link']
#    gmsg = "Search Result for <code>%s</code>:\n" % querytext
#    gmsg += "<code>%s</code>\n" % s_title
#    gmsg += "<a href='%s'>Click here</a>" % s_link
#    print(gmsg)
#    bot.sendMessage(chat_id, gmsg, reply_to_message_id=msgid, parse_mode='HTML', disable_web_page_preview='True')

def pat(bot, update):
    chat_id = update.message.chat.id
    msgid = update.message.message_id
    from_id = update.message.from_user.id
    from_user_name = update.message.from_user.first_name
    if update.message.from_user.last_name is not '':
        from_user_name += " " + update.message.from_user.last_name
    chat_type = update.message.chat.type
    reply_to = update.message.reply_to_message
    if reply_to is not None:
        reply_to_id = reply_to.message_id
        to_user = reply_to.from_user
        to_user_id = to_user.id
        to_user_name = to_user.first_name
        if to_user.last_name is not '':
            to_user_name += " " + to_user.last_name
    
    add(update.message)   
    
    bye = checkbanned(from_id)
    if bye == 1:
        return
        
    sql = "select count(patid) from patdb"
    try:
        cursor.execute(sql)
        data = cursor.fetchall()
        for row in data:
            patcount = row[0]
    except:
        print("ERROR at count pat desc")

    patnum = random.randint(1, patcount)

    sql2 = "select patdesc from patdb where patid = '%d'" % (patnum)
    try:
        cursor.execute(sql2)
        data = cursor.fetchall()
        for row in data:
            patdesc = row[0]
    except:
        print("ERROR")
    if reply_to is None:
        bot.sendMessage(chat_id, '* pats pats *')
    else:
        patmsg = to_user_name
        patmsg += " "
        patmsg += patdesc
        patmsg += " "
        patmsg += from_user_name
        bot.sendMessage(chat_id, patmsg, reply_to_message_id=reply_to_id)
        patcountadd=("update user set pattedby = (pattedby + 1) where telegramid=%d" % to_user_id)
        patbycountadd=("update user set patted = (patted + 1) where telegramid=%d" % from_id)
        try:
            cursor.execute(patcountadd)
            cursor.execute(patbycountadd)
            db2.commit()
        except:
            print("ERROR AT ADD PAT COUNT")


def feedback(bot, update, args):
    chat_id = update.message.chat.id
    msgid = update.message.message_id
    from_id = update.message.from_user.id
    from_name = update.message.from_user.first_name
    if update.message.from_user.last_name is not '':
        from_name += " " + update.message.from_user.last_name
    from_username =  update.message.from_user.username
    add(update.message)   
    
    bye = checkbanned(from_id)
    if bye == 1:
        return
        
    if update.message.from_user.last_name is not '':
        from_name += " " + update.message.from_user.last_name
    
    if not args:
        update.message.reply_text("Use `/feedback <Message here>` to send feedback to me!", parse_mode='Markdown')
    else:
        msg = "FEEDBACK FROM: %s (%d)\n" % (from_name, from_id)
        msg += " ".join(args)
        bot.sendMessage(chat_id=ADMIN_ID, text=msg)
        fbmessage = db2.escape_string(" ".join(args))
        fbsql = "insert into feedback (message, name, username, telegramid) values ('%s', '%s', '%s', %d)" % (fbmessage, from_name, from_username, from_id)
        cursor.execute(fbsql)
        db2.commit()
        bot.sendMessage(chat_id, "Feedback sent!", reply_to_message_id=msgid)

def jsql(bot, update, args):
    chat_id = update.message.chat.id
    msgid = update.message.message_id
    from_id = update.message.from_user.id
    
    add(update.message)   
    
    bye = checkbanned(from_id)
    if bye == 1:
        return
        
    if from_id != ADMIN_ID:
        bot.sendMessage(chat_id, ("You are not %s!" % ADMIN_NAME), reply_to_message_id=msgid)
        return
    try:
        enteredsql = " ".join(args)
        print(enteredsql)
        cursor.execute(enteredsql)
        db2.commit()
        result = cursor.fetchone()
        sqlmsg = "PERFORMING SQL QUERY:\n"
        colnames= [i[0] for i in cursor.description]
        sqlmsg += "`" + str(colnames) + "`\n"
        while result is not None:
           sqlmsg = sqlmsg + "`" + str(result) + "`"
           sqlmsg = sqlmsg + "\n"
           result = cursor.fetchone()
        sqlmsg = sqlmsg + "`num of affected rows: "+ str(cursor.rowcount) + "`"
        bot.sendMessage(chat_id, sqlmsg, reply_to_message_id=msgid, parse_mode="Markdown")
    except pymysql.MySQLError as e:
        code, errormsg = e.args
        sqlerror = "`MySQL ErrorCode: %s\nErrorMsg: %s`" % (code, errormsg)
        bot.sendMessage(chat_id, sqlerror, reply_to_message_id=msgid, parse_mode='Markdown')

def patstat(bot, update):
    from_id = update.message.from_user.id
    chat_id = update.message.chat.id
    msgid = update.message.message_id
    from_user_name = update.message.from_user.first_name
    if update.message.from_user.last_name is not '':
        from_user_name += " " + update.message.from_user.last_name
    add(update.message)
    
    bye = checkbanned(from_id)
    if bye == 1:
        return
    
    cursor2 = db2.cursor(pymysql.cursors.DictCursor)
    checkpatcount=("select patted, pattedby from user where telegramid=%d" % from_id)
    cursor2.execute(checkpatcount)
    patcount = cursor2.fetchall()
    for row in patcount:
       pats = row["patted"]
       patsby = row["pattedby"]
       patcountstr="Hello %s!\nYou have patted others `%d` times and got patted by others `%d` times." % (from_user_name, pats, patsby)
       bot.sendMessage(chat_id, patcountstr, reply_to_message_id=msgid, parse_mode="Markdown")

def myloc(bot, update, args):
    from_id = update.message.from_user.id
    chat_id = update.message.chat.id
    msgid = update.message.message_id
    
    add(update.message)
    
    bye = checkbanned(from_id)
    if bye == 1:
        return
    
    if not args:
        bot.sendMessage(chat_id, "Please use `/myloc <location>` to set your location.", reply_to_message_id=msgid, parse_mode='Markdown')
        return
    else:
        setloc = db2.escape_string(" ".join(args))
        setlocsql = "update user set loc='%s' where telegramid=%d" % (setloc, from_id)
        cursor.execute(setlocsql)
        db2.commit()
        setmsg = "Your location is set to `%s`" % setloc
        bot.sendMessage(chat_id, setmsg, reply_to_message_id=msgid, parse_mode='Markdown')
       
def now(bot, update, args):
    from_id = update.message.from_user.id
    chat_id = update.message.chat.id
    msgid = update.message.message_id
    
    add(update.message)
    
    bye = checkbanned(from_id)
    if bye == 1:
        return
    try:
        if args:
            loc = " ".join(args)
        elif not args:
            checkloc="select loc from user where telegramid=%d" % from_id
            cursor.execute(checkloc)
            db2.commit()
            result = cursor.fetchall()
            for row in result:
                userloc = row[0]
            db2.commit()
            if userloc == None:
                bot.sendMessage(chat_id, "Please use `!myloc <location>` to set default location or use `!now <location>`.", reply_to_message_id=msgid, parse_mode='Markdown')
                return
            else:
                loc = userloc
        
        url = "http://dataservice.accuweather.com/locations/v1/search"
        ran = random.randint(0,1)
        if ran == 0:
            apikey = ACCU_API_1
        else:
            apikey = ACCU_API_2
        url += "?apikey=" + apikey
        url += "&q=" +  urllib.parse.quote(loc)
        response = requests.get(url)
        result = response.json()
        locationkey = result[0]['Key']
        place = result[0]['LocalizedName'] + ", " + result[0]['AdministrativeArea']['LocalizedName'] + ", " + result[0]['Country']['LocalizedName']
        localtzname = result[0]['TimeZone']['Name']
        localtz = pytz.timezone(localtzname)
        local = str(datetime.datetime.now(localtz))
        url = "http://dataservice.accuweather.com/currentconditions/v1/"
        url += locationkey
        url += "?apikey=" + apikey
        response = requests.get(url)
        result = response.json()
        localdate = local.split(" ", 1)[0]
        localtimeandzone = local.split(" ", 1)[1]
        localtime = localtimeandzone[:8]
        localzone = localtimeandzone[-6:]
        weather = result[0]['WeatherText']
        ctemp = str(result[0]['Temperature']['Metric']['Value']) + "°" + result[0]['Temperature']['Metric']['Unit']
        ftemp = str(result[0]['Temperature']['Imperial']['Value']) + "°" + result[0]['Temperature']['Imperial']['Unit']
        wmsg = "Currently at: %s" % place
        wmsg += "\nTemperature:`\t%s or %s`" % (ctemp, ftemp)
        wmsg += "\nDescription:`\t%s`" % weather
        wmsg += "\nLocal Time:`\t%s (UTC%s)`" % (localtime, localzone)
        bot.sendMessage(chat_id, wmsg, reply_to_message_id=msgid, parse_mode='Markdown')
    except:
        print("LOL")
        bot.sendMessage(chat_id, "Something wrong with your location...", reply_to_message_id=msgid)    
        
        
def checkbanned(from_id):
    from_id =int(from_id)
    bansql = "select banned from user where telegramid=%d" % from_id
    cursor.execute(bansql)
    try:
        banned = cursor.fetchall()
        for row in banned:
            ban = row[0]
        db2.commit()
        return ban
    except:
        return -1

def jban(bot, update, args):
    from_id = update.message.from_user.id
    chat_id = update.message.from_user.id
    msgid = update.message.message_id
    
    add(update.message)
    
    bye = checkbanned(from_id)
    if bye == 1:
        return
    
    if from_id != ADMIN_ID:
        bot.sendMessage(chat_id, "You are not %s!" % ADMIN_NAME, reply_to_message_id=msgid)
        return
        
    if not args:
        bot.sendMessage(chat_id, "Use `/jban <id>`", reply_to_message_id=msgid, parse_mode="Markdown")
        return
    elif args[0] is not None:
        banid = args[0]
        print(banid)
        if banid.isdigit():
            banid = int(banid)
            if checkbanned(banid) == 1:
                print("ban already")
                update.message.reply_text("User banned already")
            elif checkbanned(banid) == -1:
                print("id wrong")
                update.message.reply_text("ID wrong")
            else:
                print("now banning")
                bannow = "update user set banned=1 where telegramid=%d" % banid
                try:
                    cursor.execute(bannow)
                    db2.commit()
                    print("banned")
                    update.message.reply_text("Ban Successful.")
                except:
                    print("fail")
                    update.message.reply_text("Failed. Try again.")
        else:
            print("not id")
            update.message.reply_text("not an id")

def junban(bot, update, args):
    from_id = update.message.from_user.id
    chat_id = update.message.from_user.id
    msgid = update.message.message_id
    
    add(update.message)
    
    bye = checkbanned(from_id)
    if bye == 1:
        return
    
    if from_id != ADMIN_ID:
        update.message.reply_text("You are not %s!" % ADMIN_NAME) 
        return
        
    if not args:
        update.message.reply_text("Use `/junban <id>`", parse_mode='Markdown')
        return
    elif args[0] is not None:
        unbanid = args[0]
        if unbanid.isdigit():
            unbanid = int(unbanid)
            if checkbanned(unbanid) == 0:
                update.message.reply_text("User was not banned")
            elif checkbanned(unbanid) == -1:
                update.message.reply_text("ID Wrong")
            else:
                unbannow = "update user set banned=0 where telegramid=%d" % unbanid
                try:
                    cursor.execute(unbannow)
                    db2.commit()
                    update.message.reply_text("Unban Successful")
                except:
                    update.message.reply_text("Failed, try again.")
        else:
            print("not id")
            update.message.reply_text("Not ID")

def jbanlist(bot, update):
    from_id = update.message.from_user.id
    chat_id = update.message.chat.id
    msgid = update.message.message_id
    
    add(update.message)
    
    bye = checkbanned(from_id)
    if bye == 1:
        return
    
    if from_id != ADMIN_ID:
        bot.sendMessage(chat_id, "You are not %s!" % ADMIN_NAME, reply_to_message_id=msgid)
        return
        
    banlistsql = "select name, username, telegramid from user where banned=1"
    cursor.execute(banlistsql)
    db2.commit()
    result=cursor.fetchone()
    sqlmsg = "Banned users:\n"
    if result == None:
        sqlmsg  = "No banned users"
    while result is not None:
        sqlmsg+="`"+str(result)+"`\n"
        result=cursor.fetchone()
    bot.sendMessage(chat_id, sqlmsg, reply_to_message_id=msgid, parse_mode='Markdown')

def nopm(bot, chat_id, from_name, msgid):
    nopmmsg = from_name + ", Please start me at PM first."
    keyboard = [[InlineKeyboardButton("Start Me!", callback_data = 'start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.sendMessage(chat_id, nopmmsg, reply_to_message_id=msgid, reply_markup=reply_markup)

def button(bot, update):
    query = update.callback_query
    queryid = query.id
    query_from_id = query.from_user.id
    query_from_first = query.from_user.first_name
    query_from_last = query.from_user.last_name
    if query_from_last is not '':
        query_from_name = query_from_first + " " + query_from_last
    else:
        query_from_name = query_from_first
    msg = query.message
    chat_id = msg.chat.id
    msgid = msg.message_id
    tomsg = query.message.reply_to_message
#    from_id = chat_data['from_id']
    
    if query.data == 'start':
        starturl="telegram.me/" + BOT_USERNAME + "?start=help"
        bot.answerCallbackQuery(queryid, url = starturl)

    if query.data == 'achv':
        starturl="telegram.me/" + BOT_USERNAME + "?start=achv"
        bot.answerCallbackQuery(queryid, url=starturl)
        
def help(bot, update):
    chat_type = update.message.chat.type
    from_id = update.message.from_user.id
    chat_id = update.message.chat.id
    from_name = update.message.from_user.first_name
    msgid = update.message.message_id
    
    add(update.message)
    
    bye = checkbanned(from_id)
    if bye == 1:
        return
    
    helpmsg = "Availble Commands:\n"
    helpmsg += "`/pat: [single use or by reply], pats someone`\n"
    helpmsg += "`/patstat: chat your pat history`\n"
    helpmsg += "`/myloc <location>: set your current location for using /now`\n"
    helpmsg += "`/now (<location>): return current weather for your already set location (or inputted location)`\n"
    helpmsg += "`/feedback <message>: send feedback to me!`\n"
    helpmsg += "`/t <text>: (or by reply), translate to english`"
#    print(helpmsg)
#    try:
    bot.sendMessage(from_id, helpmsg, parse_mode='Markdown')
    if chat_type != 'private':
        bot.sendMessage(chat_id, "I've sent you the help message in private.", reply_to_message_id=msgid)
#    except:
#        if chat_type != 'private':
#            nopm(bot, chat_id, from_name, msgid)

def send(bot, update, args):
    chat_type = update.message.chat.type
    from_id = update.message.from_user.id
    chat_id = update.message.chat.id
    from_name = update.message.from_user.first_name
    msgid = update.message.message_id
    reply_to = update.message.reply_to_message
    if reply_to is not None:
        to_user_id = reply_to.from_user.id
    
    add(update.message)
    
    bye = checkbanned(from_id)
    if bye == 1:
        return
    
    if from_id != ADMIN_ID:
        bot.sendMessage(chat_id, ("You are not %s!" % ADMIN_NAME), reply_to_message_id=msgid)
        return
        
    if reply_to is None:
        if not args:
            bot.sendMessage(chat_id, "Use `/send <id> <message>`", reply_to_message_id=msgid, parse_mode='Markdown')
            return
        if len(args) <= 1:
            bot.sendMessage(chat_id, "Use `/send <id> <message>`", reply_to_message_id=msgid, parse_mode='Markdown')
            return
        sendperson = args[0]
        args.pop(0)
        sendmessage = " ".join(args)
#        personplusmessage = after_command

        if sendperson.isdigit():
            try:
                bot.sendMessage(sendperson, sendmessage)
                bot.sendMessage(chat_id, "Message sent", reply_to_message_id=msgid)
            except:
                bot.sendMessage(chat_id, "Send Failed", reply_to_message_id=msgid)
        elif sendperson[1:].isdigit():
                bot.sendMessage(sendperson, sendmessage)
                bot.sendMessage(chat_id, "Message sent")
        else:
            sendperson = sendperson[1:]
            personsql="select telegramid from user where username='%s'" % sendperson
            cursor.execute(personsql)
            db2.commit()
            result = cursor.fetchall()
            for row in result:
                item = row[0]
            db2.commit()
            try:
                bot.sendMessage(item, sendmessage)
                bot.sendMessage(chat_id, "Message sent", reply_to_message_id=msgid)
            except:
                bot.sendMessage(chat_id, "Send Failed", reply_to_message_id=msgid)
    else:
        sendperson = to_user_id
        sendmessage = " ".join(args)
        if reply_to.forward_from is not None:
            sendperson = reply_to.forward_from.id
        try:
            bot.sendMessage(sendperson, sendmessage)
            bot.sendMessage(chat_id, "Message sent", reply_to_message_id=msgid)
        except:
            bot.sendMessage(chat_id, "Send Failed", reply_to_message_id=msgid)

def main():
    global db2, cursor
    db2 = pymysql.connect(MYSQL_SERVER, MYSQL_USERNAME, MYSQL_PW, MYSQL_DBNAME, charset='utf8', autocommit=True)
    cursor = db2.cursor()
    
    cursor.execute("set names utf8mb4")
    cursor.execute("set character set utf8mb4")
    cursor.execute("set character_set_connection=utf8mb4")

    cursor.execute(SQL_CREATE_TABLE_1)
    cursor.execute(SQL_CREATE_TABLE_2)
    cursor.execute(SQL_CREATE_TABLE_3)
    cursor.execute(SQL_CREATE_TABLE_4)
    db2.commit()
    
    
    try:
        cursor.execute(SQL_DEFAULT_PAT)
        db2.commit()
#        db2.close()
    except:
        print("Default Pat String exists already.")
        
    updater = Updater(BOT_TOKEN)

    job = updater.job_queue
    nexthour = datetime.datetime.now().replace(microsecond=0).replace(second=0).replace(minute=0) + datetime.timedelta(hours=1)
#    job.run_repeating(amaat, datetime.timedelta(hours=1), first=nexthour)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("jbanlist", jbanlist))
    dp.add_handler(CommandHandler("junban", junban, pass_args=True))
    dp.add_handler(CommandHandler("jban", jban, pass_args=True))
    dp.add_handler(CommandHandler("now", now, pass_args=True))
    dp.add_handler(CommandHandler("jsql", jsql, pass_args=True))
    dp.add_handler(CommandHandler("patstat", patstat))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("feedback", feedback, pass_args=True))
    dp.add_handler(CommandHandler("t", translatee, pass_args=True))
    dp.add_handler(CommandHandler("myloc", myloc, pass_args=True))
#    dp.add_handler(CommandHandler("pat", pat))
    dp.add_handler(RegexHandler("^[!/][Pp][Aa][Tt]", pat))
    dp.add_handler(CommandHandler("send", send, pass_args=True))
    dp.add_handler(CommandHandler("corgi", corgii))
    dp.add_handler(CommandHandler("re", repeat, pass_args=True))
    dp.add_handler(CommandHandler("tg", tg))
    dp.add_handler(CommandHandler("z", showinfo))
    dp.add_handler(CommandHandler("dict", dict, pass_args=True))
    dp.add_handler(CommandHandler("achv", achv))
    dp.add_handler(CommandHandler("ud", ud, pass_args=True))
    
    money_regex="^[\s]*(?P<amount>[0-9,.]+)[\s]*(?P<a>[A-Za-z]+)[\s]+[tT][oO][\s]+(?P<b>[A-Za-z]+)$"
    dp.add_handler(RegexHandler(money_regex, money, pass_groupdict=True))
    
    dp.add_handler(CallbackQueryHandler(button))
    
    dp.add_error_handler(error)
    
    updater.start_polling()
    print("Bot has started... Polling for messages...")
    updater.idle()



if __name__ == '__main__':
    main()
