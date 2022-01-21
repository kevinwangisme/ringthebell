import discord
import os
#import pynacl
#import dnspython
import server
from discord.ext import commands
from datetime import datetime
import requests
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


intents = discord.Intents.default()
intents.members = True   # enable intents.members
intents.presences = True

keb_discord_id = '850531886261600276'
kv_discord_id = '742820006831587438'
kt_discord_id = '429757950618238987'
bot_discord_id = '922701449580937268'

#client = discord.Client()
#client = discord.Client(, intents=intents)

# return current utc-time string
def get_cur_utctime():
  dt = datetime.utcnow()
  #print(dt)
  cur_utctime_str = str('{:04}'.format(dt.year) + '-' + '{:02}'.format(dt.month) + '-' + '{:02}'.format(dt.day) + '-' + '{:02}'.format(dt.hour) + ':' + '{:02}'.format(dt.minute) + ':' + '{:02}'.format(dt.second) + '.' + '{:06}'.format(dt.microsecond))

  #print(qid)
  return cur_utctime_str
  


# Firestore operations
cred = credentials.Certificate('credentials.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

Students_ref = db.collection(u'Students')
Tutors_ref = db.collection(u'Tutors')
Questions_ref = db.collection(u'Questions')


def DBG_add_a_student(name, school, grade, discord_id, discord_name):
  print('Add student, name=', name, ', school=', school, ', grade=', grade, ', discord_id=', discord_id, ', discord_name=', discord_name)
  student_s = {
    u'discord_id':discord_id,
    u'discord_name':discord_name,
    u'discord_status':'',
    u'name':name,
    u'school':school,
    u'grade':grade,
    u'tutor_preferences':'',
    u'profile_info':'',
    u'rank':0,
    u'total_scores_badages':'',
    u'total_questions':0,
    u'total_sessions':0,
    u'total_session_minutes':0,
    u'total_wait_minutes':0
  }

  req_ref = Students_ref.document(discord_id)
  req_ref.set(student_s)
  show_collection(Students_ref)


def DBG_add_a_tutor(name, school, grade, discord_id, discord_name, tutor_subjects):
  print('Add tutor, name=', name, ', school=', school, ', grade=', grade, ', discord_id=', discord_id, ', discord_name=', discord_name)
  tutor_s = {
    u'discord_id':discord_id,
    u'discord_name':discord_name,
    u'discord_status':'',
    u'name':name,
    u'school':school,
    u'grade':grade,
    u'tutor_subjects':tutor_subjects,
    u'tutor_course_names':'',
    u'tutor_preferences':'',
    u'tutor_grades':'',
    u'profile_info':'',
    u'rank':0,
    u'total_scores':0,
    u'total_matches':0,
    u'total_pickups':0,
    u'total_sessions':0,
    u'total_session_minutes':0,
    u'total_unquestioned_logins':0,
    u'got_a_match':False,
    u'pickedup_a_question':False,
  }

  req_ref = Tutors_ref.document(discord_id)
  req_ref.set(tutor_s)
  show_collection(Tutors_ref)


DBG_CNT = 1
def show_collection(collection_ref):
  global DBG_CNT
  print(DBG_CNT, ': show collection: ', collection_ref)
  DBG_CNT = DBG_CNT + 1
  docs = collection_ref.stream()
  cnt = 0
  for doc in docs:
    cnt = cnt + 1
    print(f'{cnt}: {doc.id} => {doc.to_dict()}')
    #dict = doc.to_dict()
    #print('to_dict: ', dict)
    #print('======discord_id=', doc.to_dict()['discord_id'])
  print('Total records: ', cnt)


def match_tutors(student_id, subject):
  # matching_tutors here
  matched_tutors = []
  print('match_tutors: student_id=', student_id, ', subject=', subject)
  t_ref = Tutors_ref.where(u'tutor_subjects', u'array_contains', subject).stream()
  #t_ref = Tutors_ref.where(u'tutor_subjects', u'array_contains', u'apcs').stream()
  for t in t_ref:
    t_dict = t.to_dict()
    #print(f'Found record t: {t_dict}')
    t_discord_status = t_dict['discord_status']
    t_discord_name = t_dict['discord_name']
    if (t_discord_status == u'dnd'):
      print(f'Skip tutor: {t_discord_name}: status={t_discord_status}')
      continue
    t_subjects = t_dict['tutor_subjects']
    t_discord_id = t_dict['discord_id']
    print(f'Found matching tutor subjects= {t_subjects} discord_id= {t_discord_id}')
    matched_tutors.append(t_discord_id)
  print(matched_tutors)
  return matched_tutors



def delete_documents_in_collection(collection_ref, batch_size):
  print('In delete_documents_in_collection:')
  docs = collection_ref.limit(batch_size).stream()
  deleted = 0
  for doc in docs:
    print(f'{deleted+1}: deleting doc {doc.id} => {doc.to_dict()}')
    doc.reference.delete()
    deleted = deleted + 1



def DBG_initialization():
  if (False):

    delete_documents_in_collection(Students_ref, 10)
    delete_documents_in_collection(Tutors_ref, 10)
    DBG_add_a_student("fledgling_a", "Sun1", 5, keb_discord_id, "keb#0598")
    DBG_add_a_student("fledgling_b", "Sun2", 8, kt_discord_id, "kaitlynッ#2666")
    tutor_subjects=[]
    tutor_subjects.append('apcs')
    print(tutor_subjects)
    DBG_add_a_tutor("veteran_x", "Sun3", 10, kv_discord_id, "Kevin Wang#8725", tutor_subjects)

    delete_documents_in_collection(Questions_ref, 10)
    show_collection(Questions_ref)

  show_collection(Tutors_ref)
  matched_tutors = match_tutors("test_user_id", "apcs")
  return matched_tutors




def get_quote():
  response = requests.get("https://zenquotes.io/api/random")
  json_data = json.loads(response.text)
  quote = json_data[0]['q'] + " -" + json_data[0]['a']
  return quote


def add_question(question_id, student_id, args):
  print('====add_question====: ', student_id, args)
  q_timestamp = 0 
  subject = ''
  for arg in args:
    if (subject == ''):
      subject = arg
      break

  print('Add question, question_id=', question_id, ', subject=', subject, ', q_timestamp=', q_timestamp)
  question_s = {
    u'status':u'new',
    u'question_id':question_id,
    u'student_id':student_id,
    u'tutor_id':'',
    u'subject':subject,
    u'extra_info':'',
    u'message':args,
    u'images':'',
    u'question_time':q_timestamp,
    u'picked_up_time':'',
    u'session_start_time':'',
    u'session_complete_time':'',
    u'session_minutes':0,
    u'service_minutes':0,
    u'score':0,
    u'tutor_feedback':'',
    u'student_feedback':'',
    u'connection_method':'',
    u'session_result':'',
    u'session_logs':'',
    u'session_recordings':'',
    u'skip_tutors':[],
    u'matched_tutors':[]}

  req_ref = Questions_ref.document(question_id)
  req_ref.set(question_s)
  show_collection(Questions_ref)

 

def update_question(question_id, update_s):
  print('====update_question====: ', question_id, update_s)
  q_ref = Questions_ref.document(question_id)
  #req_ref = Questions_ref.where(u'question_id', u'==', question_id)
  #q_ref.update({
  #  u'tutor_id': tutor_id,
  #  u'status': 'picked-up',
  #  u'picked_up_time':'',
  #  })
  q_ref.update(update_s)
  show_collection(Questions_ref)


def get_student_id_str_from_question_id(question_id):
  print('====get_student_id_from_question_id====: ', question_id)
  q_ref = Questions_ref.document(question_id)
  #req_ref = Questions_ref.where(u'question_id', u'==', question_id)
  doc = q_ref.get()
  print(f'{doc.id} => {doc.to_dict()}')
  question = doc.to_dict()
  student_id_str = question['student_id']
  print('question student_id=', student_id_str)
  print(f'Found questions with {question_id}, student_id = {student_id_str}')
  return str(student_id_str)



#async def get_member_from_id_ctx(ctx: commands.Context, discord_id):
#all_members = ctx.bot.get_all_members()
async def get_member_from_id(bot, discord_id):
  print('In get_member_from_id_bot, looking for ', discord_id)
  all_members = bot.get_all_members()
  for member in all_members:
    print(member.name, member.id)
    if (str(member.id) == discord_id):
      print('found member ', discord_id, member.name)
      return member
  return None



async def create_private_channel(guild, student_id, tutor_id):
  
  #tutor_id =   kv_discord_id
  #student_id = keb_discord_id
  
  print(f'create_private_channel: got tutor={tutor_id}, student={student_id}')

  tutor_member = await get_member_from_id(bot, tutor_id)
  student_member = await get_member_from_id(bot, student_id)
  if (False):
    invitelink = 'test invite link'
    print('private channel: student_member:')
    print(student_member.name, student_member.id)
    await student_member.create_dm()
    await student_member.dm_channel.send(invitelink)
    print('private channel: tutor_member:')
    print(tutor_member.name, tutor_member.id)
    await tutor_member.create_dm()
    await tutor_member.dm_channel.send(invitelink)

  category_name = "study_room"
  category = discord.utils.get(guild.categories, name=category_name)
  #user = ctx.author.id
  overwrites = {
    guild.default_role: discord.PermissionOverwrite(read_messages=False),
    guild.me: discord.PermissionOverwrite(read_messages=True),
    #ctx.author: discord.PermissionOverwrite(read_messages=True),
    student_member: discord.PermissionOverwrite(read_messages=True),
    tutor_member: discord.PermissionOverwrite(read_messages=True)}


  if category is None: #If there's no category matching with the `name`
    print(f'creating category {category_name}')
    category = await guild.create_category(category_name, overwrites=None, reason=None)

  #channel = await guild.create_text_channel(tutor_id, overwrites=overwrites, reason=None, category=category)
  channel = await guild.create_voice_channel(tutor_id, overwrites=overwrites, reason=None, category=category)
  print(f'private_channel id= {channel.id}, name={channel.name}')
  print(f'PC: channel.category={channel.category}')

  invitelink = await channel.create_invite(max_uses=1,unique=True)
  print(f'channel: {channel}, category: {category_name}, invitelink={invitelink}')
  #await ctx.author.send(invitelink)

  print('private channel: student_member:')
  print(student_member.name, student_member.id)
  await student_member.create_dm()
  await student_member.dm_channel.send(invitelink)
  print('private channel: tutor_member:')
  print(tutor_member.name, tutor_member.id)
  await tutor_member.create_dm()
  await tutor_member.dm_channel.send(invitelink)




bot = commands.Bot(command_prefix="!", intents=intents)
@bot.command(name="hello")
async def hello_world(ctx: commands.Context, *, message):
  #got command hello_world: ctx.author.id= 429757950618238987 keb keb#0598
  await ctx.send(f'got cmd hello from {ctx.author.id} {ctx.author.name} {ctx.author}')
  await ctx.send(f'got message: {message}')
  await ctx.send(f'message.Attachment.size={message.Attachment.size}')
  #await ctx.send(f'got attachments: {message.attachments}')
  #await get_member_from_id(ctx.bot, kv_discord_id)


@bot.command(
  name="QUES",
	help="Ask a question, syntax: <subject> <msg>.",
	brief="Ask a question."
)
async def ask_question(ctx, *args):
  discord_id = ctx.author.id
  discord_name = ctx.author
  question_msg = ''
  subject = ''
  for arg in args:
    if (subject == ''):
      subject = arg
    question_msg = question_msg + ' ' + arg

  question_id = get_cur_utctime()
  await ctx.channel.send(f'Gen question_id: {question_id} for question from {discord_name}: {question_msg}')
  add_question(question_id, discord_id, args)

  # return tutor discord_ids
  matched_tutors = match_tutors(discord_id, subject)
  print('matched_tutors returned: ', matched_tutors)
  for tutor_discord_id in matched_tutors:
    print('tutor_discord_id = ', tutor_discord_id)
    member = await get_member_from_id(ctx.bot, tutor_discord_id)
    await member.create_dm()
    await member.dm_channel.send(
      f'Hi {member.name}, You are matched to question_id {question_id}: {question_msg}!'
    )




@bot.command(
  name="ANS",
	help="Answer the quesion with given question_ID, syntax: ANS <QID>",
	brief="ANS the question with given question_ID."
)
async def answer_question(ctx, question_id): 
  tutor_discord_id_str = str(ctx.author.id)
  tutor_discord_name = ctx.author
  pickup_time = get_cur_utctime()
  await ctx.channel.send(f'Answering question {question_id} from tutor {tutor_discord_name} {tutor_discord_id_str}')

  update_s = {
    u'status':u'picked-up',
    u'tutor_id':tutor_discord_id_str,
    u'picked_up_time':pickup_time,
  }
  update_question(question_id, update_s)
  ## TODO: transaction
  student_discord_id_str = get_student_id_str_from_question_id(question_id)
  
  for guild in bot.guilds:
    print(f'bot.guild={guild}')         #Ring a Bell
    print(f'bot.guild.id={guild.id}')   #922560105650733066
    #student_discord_id = keb_discord_id
    #tutor_id =   kv_discord_id
    await create_private_channel(guild, student_discord_id_str, tutor_discord_id_str)
    break

  


@bot.command(
  name="SMINUTES",
	help="Set service minutes for the quesion with given question_ID, syntax: SMINUTES <QID>",
	brief="Set service minutes for the question with given question_ID."
)
async def shour_question(ctx, question_id, service_minutes): 
  await ctx.channel.send(f'Set service minutes {service_minutes} for question {question_id}')
  update_s = {
    u'service_minutes':service_minutes,
  }
  update_question(question_id, update_s)



@bot.command(
  name="SCORE",
	help="Set score for the quesion with given question_ID, syntax: SCORE <QID>",
	brief="Set score for the question with given question_ID."
)
async def score_question(ctx, question_id, score): 
  await ctx.channel.send(f'Set score {score} for question {question_id}')
  update_s = {
    u'score':score,
  }
  update_question(question_id, update_s)



@bot.command(
  name="DBG_SESSION",
	help="Create a session for the (student, tutor) for the given question_ID, syntax: SESSION <QID>",
	brief="Create a session for (student,tutor) for the given question_ID."
)
#async def create_session(ctx, question_id, student_id, tutor_id):
  #await ctx.channel.send(f'Create private session for student: tutor: question {student_id}:{tutor_id}:{question_id}')
async def DBG_create_session(ctx, question_id, student_id, tutor_id):
  print(f'ctx.author.name= {ctx.author.name}, ctx.message.guild={ctx.message.guild}')
  for guild in bot.guilds:
    print(f'bot.guild={guild}')         #Ring a Bell
    print(f'bot.guild.id={guild.id}')   #922560105650733066

    student_id = keb_discord_id
    tutor_id =   kv_discord_id
    await create_private_channel(guild, student_id, tutor_id)

  #session_start_time = get_cur_utctime()
  #update_s = {
  #  u'status':u'in-session',
  #  u'session_start_time':session_start_time,
  #}
  #update_question(question_id, update_s)


@bot.command(
  name="DBG_SEND",
	help="DBG send cmd",
	brief="DBG send cmd"
)
async def dbg_send_cmd(ctx, *, message):
    #for member in ctx.guild.members:
    #  if (member.id != ctx.author.id):
        #channel = await member.create_dm()
        #await channel.send(message)
    #    await member.create_dm()
    #    await member.channel.send(message)
    #await ctx.send('Messages successfully sent!')
    dm = await ctx.author.create_dm()
    await dm.send('test message')
   

@bot.event
async def on_ready():
  await bot.change_presence(activity=discord.Streaming(name="Tutorials", url="http://www.twitch.tv/accountname"))
  print('We have logged in as {0.user}'.format(bot), ' Bot ID: {}'.format(bot.user.id))

  if (False):
    for guild in bot.guilds:
      #await guild.text_channels[0].send('test message')
      print(f'bot.guild={guild}')         #Ring a Bell
      print(f'bot.guild.id={guild.id}')   #922560105650733066

      student_id = keb_discord_id
      tutor_id =   kv_discord_id
      await create_private_channel(guild, student_id, tutor_id)

  #DBG_initialization()

@bot.event
async def on_member_join(member):
  print(member.name, member.id, ', on_member_join: welcome to join Ring-a-Bell server!')
  await member.create_dm()
  await member.dm_channel.send(
    f'Hi {member.name}, {member.id}, welcome to join Ring-a-Bell server!'
  )


@bot.event
async def on_member_update(before, after):
  if (before.name.find('Bot') == -1):
    print('skip Bot on_member_update')
    return
  print('on_member_update before: ', before.name, before.id, before.status, before.roles)
  print('on_member_update after: ', after.name, after.id, after.status, after.roles)
  #status: offline (invisible), online, dnd, idle
  if str(after.status) == "online":
    await after.create_dm()
    await after.dm_channel.send(
      f'Hi {after.name} ({after.id}), welcome to be online on Ring-a-Bell server!'
    )

@bot.event 
async def on_voice_state_update(member, before, after):
  print('=====Private_Channel: on_voice_state_update: channel.name=tutor_id, channel.id is unique.')
  oldchan = before.channel
  newchan = after.channel
  if (oldchan is not None):
    if (oldchan.category.name == "study_room"):
      # user (either student or tutor is leaving private channel of study_room.
      member_count = len(oldchan.members)
      print(f'{member.name} is leaving')
      print(f'on_voice_state_update before: id={oldchan.id} name={oldchan.name} cat={oldchan.category}, member_count_after_leaving={member_count}')
      curutc = get_cur_utctime()
      print(f'channel created_at_UTC: {oldchan.created_at}, cur_UTC={curutc}')
      if (member_count == 0):
        print(f'deleting channel name {oldchan.name}, id={oldchan.id}')
        await before.channel.delete()

  if (newchan is not None):
    if (newchan.category.name == "study_room"):
      member_count = len(newchan.members)
      print(f'{member.name} is joining')
      print(f'on_voice_state_update after: id={newchan.id} name={newchan.name} cat={newchan.category}, member_count_after_joining={len(newchan.members)}')


  #if before.channel is None and after.channel is not None:
  #  if before.channel.id == [YOUR_CHANNEL_ID]:
  #      await member.guild.system_channel.send("Alarm!")



@bot.listen()
async def on_message(message):
  if "tutorial" in message.content.lower():
    # in this case don't respond with the word "Tutorial" or you will call the on_message event recursively
      await message.channel.send('This is what you want http://youtube.com/fazttech')
      await bot.process_commands(message)

  if message.content.startswith('image'):
      await message.channel.send(message)
      await message.channel.send(message.attachments)
      #await message.channel.send(f'message.Attachment.size={message.Attachment.size}')
      await message.channel.send(file=discord.File('IMG_2266.JPG'))

print('running bot')

server.server()
bot.run(TOKEN)
