import discord
import os
#import pynacl
#import dnspython
import server


from discord.ext import commands
import time
from datetime import datetime
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

 


# Firestore operations
cred = credentials.Certificate('bot/credentials.json')
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
    u'total_scores_badges':0,
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
  t_ref = Tutors_ref.where((u'tutor_subjects').lower(), u'array_contains', subject.lower()).stream()
  #t_ref = Tutors_ref.where(u'tutor_subjects', u'array_contains', u'apcs').stream()
  for t in t_ref:
    t_dict = t.to_dict()
    t_subjects = t_dict['tutor_subjects']
    t_discord_id = t_dict['discord_id']
    print(f'Found matching tutor subjects= {t_subjects} discord_id= {t_discord_id}')
    matched_tutors.append(t_discord_id)
  print(matched_tutors)
  return matched_tutors


async def dm_matching_questions_for_tutor(ctx, tutor_discord_id):
  print('====dm_matching_questions_for_tutor: ', tutor_discord_id)
  tutor_discord_name = ctx.author.name
  #dm = await ctx.author.create_dm()
  dm = ctx.channel

  t_ref = Tutors_ref.document(tutor_discord_id)
  doc = t_ref.get()
  tutor = doc.to_dict()
  print(f'{doc.id} => {tutor}')

  new_matches = 0
  tutor_subjects = tutor['tutor_subjects']
  q_ref = Questions_ref.where(u'status', u'==', u'new').stream() 
  for q in q_ref:
    question = q.to_dict()
    #print(f'Found question: {question}')
    q_subject = question['subject']
    if (q_subject in tutor_subjects):
      new_matches = new_matches + 1
      q_id = question['question_id']
      q_message = question['message']
      q_secs = question['question_time']
      q_time = time.asctime(time.localtime(q_secs))
      student_discord_id = question['student_id']
      dm_msg = f'Found matching question from {student_discord_id} raised at {q_time}: {q_message}, question_id={q_id}'
      print(dm_msg)
      await dm.send(dm_msg)

  print(f'Total new matches = {new_matches}')
  if (new_matches == 0):
      dm_msg = f'Have not found unassigned matching questions at present. Try again later.'
      print(dm_msg)
      await dm.send(dm_msg)
  else:
    update_tutor_total_matches(tutor_discord_name, tutor_discord_id, new_matches)



async def dm_tutor_rankings(ctx, my_discord_id):
  print('====dm_tutor_rankings: ', my_discord_id)
  #dm = await ctx.author.create_dm()
  dm = ctx.channel

  query = Tutors_ref.order_by(u'total_scores', direction=firestore.Query.DESCENDING).limit(50)
  docs = query.stream()
  dm_msg = 'Veteran:\n'
  dm_msg += 'Rank    score      veteran_discord_id                  veteran_discord_name'
  print(dm_msg)
  await dm.send(dm_msg)
  rank = 0
  for doc in docs:
    rank = rank + 1
    print(f': {doc.id} => {doc.to_dict()}')
    tutor = doc.to_dict()
    score = tutor['total_scores']
    tutor_discord_id = tutor['discord_id']
    tutor_discord_name = tutor['discord_name']
    dm_msg = f'{rank}:           {score}          {tutor_discord_id}           {tutor_discord_name}'
    if (tutor_discord_id == my_discord_id):
      dm_msg += ' ***'
    print(dm_msg)
    await dm.send(dm_msg)



async def dm_student_rankings(ctx, my_discord_id):
  print('====dm_student_rankings: ', my_discord_id)
  #dm = await ctx.author.create_dm()
  dm = ctx.channel

  query = Students_ref.order_by(u'total_scores_badges', direction=firestore.Query.DESCENDING).limit(50)
  docs = query.stream()
  dm_msg = 'Fledgling:\n'
  dm_msg += 'Rank    score      fledgling_discord_id                fledgling_discord_name'
  print(dm_msg)
  await dm.send(dm_msg)
  rank = 0
  for doc in docs:
    rank = rank + 1
    print(f': {doc.id} => {doc.to_dict()}')
    student = doc.to_dict()
    score = student['total_scores_badges']
    student_discord_id = student['discord_id']
    student_discord_name = student['discord_name']
    dm_msg = f'{rank}:           {score}           {student_discord_id}             {student_discord_name}'
    if (student_discord_id == my_discord_id):
      dm_msg += ' ***'
    print(dm_msg)
    await dm.send(dm_msg)



async def show_my_record_as_tutor(ctx, discord_id):
  print('====show_my_record_as_tutor: ', discord_id)
  discord_name = ctx.author.name
  #dm = await ctx.author.create_dm()
  dm = ctx.channel

  t_ref = Tutors_ref.document(discord_id)
  doc = t_ref.get()
  tutor = doc.to_dict()
  if (tutor == None):
    dm_msg = f'Did not find veteran record for {discord_id} {discord_name}'
    print(dm_msg)
    await dm.send(dm_msg)
    return

  print(f'{doc.id} => {tutor}')

  dm_msg = 'Veteran record for ' + discord_name + ':\n'
  dm_msg += 'Total_score: ' + str(tutor['total_scores']) + '\n' 
  dm_msg += 'Total_matches: ' + str(tutor['total_matches']) + '\n' 
  dm_msg += 'Total_pickups: ' + str(tutor['total_pickups']) + '\n' 
  await dm.send(dm_msg)
  dm_msg = ''
  dm_msg += 'Total_sessions: ' + str(tutor['total_sessions']) + '\n' 
  dm_msg += 'Total_session_minutes: ' + str(tutor['total_session_minutes']) + '\n' 
  dm_msg += 'Total_service_minutes: ' + str(tutor['total_service_minutes']) + '\n\n' 
  await dm.send(dm_msg)


async def show_my_record_as_student(ctx, discord_id):
  print('====show_my_record_as_student: ', discord_id)
  discord_name = ctx.author.name
  #dm = await ctx.author.create_dm()
  dm = ctx.channel

  s_ref = Students_ref.document(discord_id)
  doc = s_ref.get()
  student = doc.to_dict()
  if (student == None):
    dm_msg = f'Did not find fledgling record for {discord_id} {discord_name}'
    print(dm_msg)
    await dm.send(dm_msg)
    return

  print(f'{doc.id} => {student}')

  total_unanswered_questions = student['total_questions'] - student['total_sessions']

  dm_msg = 'Fledgling record for ' + discord_name + ':\n'
  dm_msg += 'Total_questions: ' + str(student['total_questions']) + '\n' 
  dm_msg += 'Total_sessions: ' + str(student['total_sessions']) + '\n' 
  await dm.send(dm_msg)
  dm_msg = ''
  dm_msg += 'Total_session_minutes: ' + str(student['total_session_minutes']) + '\n' 
  dm_msg += 'Total_unanwsered_questions: ' + str(total_unanswered_questions) + '\n' 
  dm_msg += 'Total_scores_badges: ' + str(student['total_scores_badges']) + '\n' 
  dm_msg += 'Total_wait_minutes: ' + str(total_wait_minutes) + '\n\n' 
  await dm.send(dm_msg)



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
    tutor_subjects.append('english')
    tutor_subjects.append('math')
    print(tutor_subjects)
    DBG_add_a_tutor("veteran_x", "Sun3", 10, kv_discord_id, "Kevin Wang#8725", tutor_subjects)

    delete_documents_in_collection(Questions_ref, 10)
    show_collection(Questions_ref)

  show_collection(Tutors_ref)
  matched_tutors = match_tutors("test_user_id", "english")
  return matched_tutors





def update_tutor(tutor_discord_id, update_s):
  print('====update_tutor====: ', tutor_discord_id, update_s)
  t_ref = Tutors_ref.document(tutor_discord_id)
  t_ref.update(update_s)
  show_collection(Tutors_ref)


def update_tutor_service_minutes(discord_id, service_minutes):
  print(f'====update_tutor_service_minutes: tutor {discord_id} {service_minutes}')
  t_ref = Tutors_ref.document(discord_id)
  doc = t_ref.get()
  print(f'{doc.id} => {doc.to_dict()}')
  tutor = doc.to_dict()
  total_service_minutes = tutor['total_service_minutes']
  print('total_service_minutes = ', total_service_minutes)
  discord_name = tutor['discord_name']
  print('discord_name = ', discord_name)
  new_total_service_minutes = total_service_minutes + service_minutes

  #print(f'tutor: {discord_name} {discord_id} old total_service_minutes={total_service_minutes}, new total_service_minutes={new_total_service_minutes}')
  update_s = {
    u'total_service_minutes':new_total_service_minutes
  }
  t_ref.update(update_s)
  show_collection(Tutors_ref)


def update_tutor_total_scores(discord_id, score):
  print(f'===update_tutor_total_scores: discord_id={discord_id}, score={score}')
  t_ref = Tutors_ref.document(discord_id)
  doc = t_ref.get()
  print(f'{doc.id} => {doc.to_dict()}')
  tutor = doc.to_dict()
  total_scores = tutor['total_scores']
  discord_name = tutor['discord_name']
  new_total_scores = total_scores + score

  print(f'tutor: {discord_name} {discord_id} old total_scores={score}, new total_scores={new_total_scores}')
  update_s = {
    u'total_scores':new_total_scores
  }
  t_ref.update(update_s)
  show_collection(Tutors_ref)


def update_tutor_total_pickups(discord_name, discord_id):
  t_ref = Tutors_ref.document(discord_id)
  doc = t_ref.get()
  print(f'{doc.id} => {doc.to_dict()}')
  tutor = doc.to_dict()
  total_pickups = tutor['total_pickups']
  new_total_pickups = total_pickups + 1

  print(f'tutor: {discord_name} {discord_id} old total_pickups={total_pickups}, new total_pickups={new_total_pickups}')
  update_s = {
    u'total_pickups':new_total_pickups,
    u'pickedup_a_question':True
  }
  t_ref.update(update_s)
  show_collection(Tutors_ref)




def update_tutor_total_matches(discord_name, discord_id, new_matches=1):
  t_ref = Tutors_ref.document(discord_id)
  doc = t_ref.get()
  print(f'{doc.id} => {doc.to_dict()}')
  tutor = doc.to_dict()
  total_matches = tutor['total_matches']
  new_total_matches = total_matches + new_matches

  print(f'tutor: {discord_name} {discord_id} old total_matches={total_matches}, new total_matches={new_total_matches}')
  update_s = {
    u'total_matches':new_total_matches,
    u'got_a_match':True
  }
  t_ref.update(update_s)
  show_collection(Tutors_ref)


def add_question(question_id, student_id, args):
  print('====add_question====: ', student_id, args)
  epoch_secs = time.time()
  subject = ''
  for arg in args:
    if (subject == ''):
      subject = arg
      break

  print('Add question, question_id=', question_id, ', subject=', subject, ', q_epoch_secs=', epoch_secs)
  question_s = {
    u'status':u'new',
    u'question_id':question_id,
    u'v_channel_id':'',
    u't_channel_id':'',
    u'student_id':student_id,
    u'tutor_id':'',
    u'subject':subject,
    u'extra_info':'',
    u'message':args,
    u'images':'',
    u'question_time':epoch_secs,
    u'picked_up_time':0,
    u'session_start_time':0,
    u'session_complete_time':0,
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


def get_question_tutor_and_student_id(question_id):
  print('====get_question_tutor_and_student_id: ', question_id)
  q_ref = Questions_ref.document(question_id)
  doc = q_ref.get()    
  question = doc.to_dict()
  if (question == None):
    return None, None

  student_discord_id = question['student_id']
  tutor_discord_id = question['tutor_id']
  print(f'question {question_id}: student={student_discord_id} tutor={tutor_discord_id}')
  return student_discord_id, tutor_discord_id


def update_student_total_questions(discord_id):
  s_ref = Students_ref.document(discord_id)
  doc = s_ref.get()
  print(f'{doc.id} => {doc.to_dict()}')
  student = doc.to_dict()
  total_questions = student['total_questions']
  new_total_questions = total_questions + 1
  new_total_scores_badges = new_total_questions

  print(f'student: {discord_id} total_questions old={total_questions}, new ={new_total_questions}')
  update_s = {
    u'total_questions':new_total_questions,
    u'total_scores_badges':new_total_scores_badges
  }
  s_ref.update(update_s)
  show_collection(Students_ref)



def update_student_total_wait_minutes(discord_id, wait_minutes):
  s_ref = Students_ref.document(discord_id)
  doc = s_ref.get()
  print(f'{doc.id} => {doc.to_dict()}')
  student = doc.to_dict()
  total_wait_minutes = student['total_wait_minutes']
  new_total_wait_minutes = total_wait_minutes + wait_minutes

  print(f'student: {discord_id} old total_wait_minutes={wait_minutes}, new total_wait_minutes={new_total_wait_minutes}')
  update_s = {
    u'total_wait_minutes':new_total_wait_minutes
  }
  s_ref.update(update_s)
  show_collection(Students_ref)


# Update total_sessions, total_session_minutes for the student
def update_student_total_session_minutes(discord_id, session_minutes):
    s_ref = Students_ref.document(discord_id)
    doc = s_ref.get()
    print(f'{doc.id} => {doc.to_dict()}')
    student = doc.to_dict()
    total_sessions = student['total_sessions']
    discord_name = student['discord_name']
    total_session_minutes = student['total_session_minutes']
    new_total_sessions = total_sessions + 1
    new_total_session_minutes = total_session_minutes + session_minutes
    print(f'student: {discord_name} {discord_id} new total_sessions={new_total_sessions}, total_session_minutes={new_total_session_minutes}')

    update_s = {
      u'total_sessions':new_total_sessions,
      u'total_session_minutes':new_total_session_minutes
    }
    Students_ref.document(doc.id).update(update_s)
    show_collection(Students_ref)


def update_question(question_id, update_s):
  print('====update_question====: ', question_id, update_s)
  q_ref = Questions_ref.document(question_id)
  doc = q_ref.get()    
  question = doc.to_dict()
  if (question == None):
    return None, None

  v_channel_id = question['v_channel_id']
  t_channel_id = question['t_channel_id']
  student_id = question['student_id']
  tutor_id = question['tutor_id']

  q_ref.update(update_s)
  show_collection(Questions_ref)
  return tutor_id, student_id, v_channel_id, t_channel_id




def update_voice_chan_start_questionDB(v_chan_id, member_count):
  new_status = 'session-start-' + str(member_count)
  epoch_secs = time.time()
  update_s = {
    u'status':new_status,
    u'session_start_time':epoch_secs,
  }
  print(f'====update_voice_chan_start_questionDB, v_chan_id= {v_chan_id}, member_count= {member_count}, update_s={update_s}')
  q_ref = Questions_ref.where(u'v_channel_id', u'==', v_chan_id)
  docs = q_ref.get()
  for doc in docs:
    print(f'{doc.id} => {doc.to_dict()}')
    question = doc.to_dict()
    status = question['status']
    t_chan_id = question['t_channel_id']
    print(f'question old status = {status}, v_channel_id={v_chan_id}, t_channel_id={t_chan_id} new status = {new_status}')
    Questions_ref.document(doc.id).update(update_s)
    show_collection(Questions_ref)




def update_question_session_complete(v_chan_id):
  print('====update_question_session_complete: v_channel_id=', v_chan_id)
  session_complete_time = time.time()
  q_ref = Questions_ref.where(u'v_channel_id', u'==', v_chan_id)
  docs = q_ref.get()
  print('== docs == ', docs)
  for doc in docs:
    print(f'{doc.id} => {doc.to_dict()}')
    question = doc.to_dict()
    old_status = question['status']
    tutor_discord_id = question['tutor_id']
    student_discord_id = question['student_id']
    old_session_minutes = question['session_minutes']
    print('=======question old_status =', old_status)

    if (old_status == 'session-start-2'):
      # a good session with 2 people joined, mark session-complete
      new_status = 'session-complete'
      print(f'(complete session) question status: old = {old_status}, new = {new_status}')
    else: # could be: new picked-up, session-start-1
      # keep question status unchanged so we know where it was left. (more informational than setting session-incomplete)
      print(f'(incomplete session) question status: keep old = {old_status}, no update')
      return tutor_discord_id, student_discord_id, 0

    session_start_time = question['session_start_time']
    session_minutes = (session_complete_time - session_start_time) / 60.0
    accumulated_session_minutes = old_session_minutes + session_minutes
    print(f'session_start_time={time.asctime(time.localtime(session_start_time))}')
    print(f'session_complete_time={time.asctime(time.localtime(session_complete_time))}')
    print(f'old_session_minutes={old_session_minutes}, new session_minutes={session_minutes}')
    print('updating new_status: ', new_status, ' updated session_minutes=', accumulated_session_minutes)

    update_s = {
      u'status':new_status,
      u'session_complete_time':session_complete_time,
      u'session_minutes':accumulated_session_minutes,
    }
    Questions_ref.document(doc.id).update(update_s)
    show_collection(Questions_ref)
    return tutor_discord_id, student_discord_id, session_minutes


def update_tutor_total_session_minutes(discord_id, session_minutes):
    # Update total_sessions, total_session_minutes for the tutor
    t_ref = Tutors_ref.document(discord_id)
    doc = t_ref.get()
    print(f'{doc.id} => {doc.to_dict()}')
    tutor = doc.to_dict()
    total_sessions = tutor['total_sessions']
    discord_name = tutor['discord_name']
    total_session_minutes = tutor['total_session_minutes']
    new_total_sessions = total_sessions + 1
    new_total_session_minutes = total_session_minutes + session_minutes
    print(f'tutor: {discord_name} {discord_id} new total_sessions={new_total_sessions}, total_session_minutes={new_total_session_minutes}')

    update_s = {
      u'total_sessions':new_total_sessions,
      u'total_session_minutes':new_total_session_minutes
    }
    Tutors_ref.document(doc.id).update(update_s)
    show_collection(Tutors_ref)



def get_question(question_id):
  question = Questions_ref.document(question_id).get().to_dict()
  print('====get_question: question_id=', question_id, 'question=', question)
  return question

def get_student(student_discord_id):
  student = Students_ref.document(student_discord_id).get().to_dict()
  return student

def get_tutor(tutor_discord_id):
  tutor = Tutors_ref.document(tutor_discord_id).get().to_dict()
  return tutor



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
    print('private channel: student_member: ', end='')
    print(student_member.name, student_member.id)
    await student_member.create_dm()
    await student_member.dm_channel.send(invitelink)
    print('private channel: tutor_member: ', end='')
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

  t_chan = await guild.create_text_channel(tutor_id, overwrites=overwrites, reason=None, category=category)
  t_invitelink = await t_chan.create_invite(max_uses=1,unique=True)
  print(f'priv_text_channel id= {t_chan.id}, name={t_chan.name}, cat={t_chan.category}, link={t_invitelink}')

  v_chan = await guild.create_voice_channel(tutor_id, overwrites=overwrites, reason=None, category=category)
  v_invitelink = await v_chan.create_invite(max_uses=1,unique=True)
  print(f'priv_voice_channel id= {v_chan.id}, name={v_chan.name}, cat={v_chan.category}, link={v_invitelink}')

  print(f'private channel: student: {student_member.name}, {student_member.id} -- tutor: {tutor_member.name}, {tutor_member.id}')

  await student_member.create_dm()
  await student_member.dm_channel.send(v_invitelink)
  await tutor_member.create_dm()
  await tutor_member.dm_channel.send(v_invitelink)
  
  await student_member.create_dm()
  await student_member.dm_channel.send(t_invitelink)
  await tutor_member.create_dm()
  await tutor_member.dm_channel.send(t_invitelink)
  
  return v_chan.id, t_chan.id


async def delete_private_channel_by_id(channel_id):
  private_chan = bot.get_channel(int(channel_id))
  print('channel_id = ', channel_id, ' private_chan = ', private_chan)
  if (private_chan == None):
    return

  member_count = len(private_chan.members)
  print(f'priv_channel id={private_chan.id} name={private_chan.name} cat={private_chan.category}, created_at: {private_chan.created_at}, member_count={member_count}')

  #if (member_count == 0):
  if (True):
    print(f'deleting pivate_channel name {private_chan.name}, id={private_chan.id}')
    await private_chan.delete()





bot = commands.Bot(command_prefix="!", intents=intents)
TOKEN = os.getenv("DISCORD_TOKEN")


@bot.command(name="hello")
async def hello_world(ctx: commands.Context, *, message):
  #got command hello_world: ctx.author.id= 429757950618238987 keb keb#0598
  await ctx.send(f'got cmd hello from {ctx.author.id} {ctx.author.name} {ctx.author}')
  await ctx.send(f'got message: {message}')
  await ctx.send(f'message.Attachment.size={message.Attachment.size}')


@bot.command(
  name="RING",
	help="RING: Ask a question, syntax: <subject> <msg>.",
	brief="RING: Ask a question."
)
async def ask_question(ctx, *args):
  student_discord_id = str(ctx.author.id)
  student_discord_name = ctx.author.name

  db_student_id = get_student(student_discord_id)
  if (db_student_id is None):
    await ctx.channel.send('Could not find your record as a fledgling, did you sign up for fledgling form?')
    return

  question_msg = ''
  subject = ''
  for arg in args:
    if (subject == ''):
      subject = arg
    question_msg = question_msg + ' ' + arg

  question_id = student_discord_name + '.' + str(time.time())
  await ctx.channel.send(f'Got question from {student_discord_name}: {question_msg}, generated question_id = {question_id}')
  add_question(question_id, student_discord_id, args)
  update_student_total_questions(student_discord_id)

  # return tutor discord_ids
  matched_tutor_ids = match_tutors(student_discord_id, subject)
  print('matched_tutors returned: ', matched_tutor_ids)
  for tutor_discord_id in matched_tutor_ids:
    # status: offline (invisible), online, dnd, idle
    # skip tutors in offline(invisible) and 'dnd' status (idle is ok)
    member = await get_member_from_id(ctx.bot, tutor_discord_id)
    discord_status = str(member.status)
    if (discord_status != "online" and discord_status != "idle"):
      print(f'skip tutor {member.name} {tutor_discord_id} in status ({discord_status})')
      continue

    dm_msg = f'Hi {member.name}, You are matched to question {question_msg}, question_id={question_id}'
    await member.create_dm()
    await member.dm_channel.send(dm_msg)

    update_tutor_total_matches(member.name, tutor_discord_id)




@bot.command(
  name="PICKUP",
	help="Pickup the quesion with given question_ID, syntax: PICKUP <QID>",
	brief="Pickup the question with given question_ID."
)
async def answer_question(ctx, question_id): 
  tutor_discord_id_str = str(ctx.author.id)
  tutor_discord_name = ctx.author.name
  pickup_time = time.time()
  await ctx.channel.send(f'Picking up question {question_id} from tutor {tutor_discord_name} {tutor_discord_id_str}')

  question = get_question(question_id)
  student_discord_id_str = question['student_id']
  question_time = question['question_time']
  wait_minutes = (pickup_time - question_time) / 60.0

  for guild in bot.guilds:
    print(f'bot.guild={guild}')         #Ring a Bell
    print(f'bot.guild.id={guild.id}')   #922560105650733066
    #student_discord_id = keb_discord_id
    #tutor_id =   kv_discord_id
    v_chan_id, t_chan_id = await create_private_channel(guild, student_discord_id_str, tutor_discord_id_str)
    break

  # Update question and Tutor database
  v_channel_id = str(v_chan_id)
  t_channel_id = str(t_chan_id)
  update_s = {
    u'status':u'picked-up',
    u'tutor_id':tutor_discord_id_str,
    u'v_channel_id':v_channel_id,
    u't_channel_id':t_channel_id,
    u'picked_up_time':pickup_time,
  }
  update_question(question_id, update_s)
  ## TODO: transaction
  update_tutor_total_pickups(tutor_discord_name, tutor_discord_id_str)
  update_student_total_wait_minutes(student_discord_id_str, wait_minutes)


  


@bot.command(
  name="SMINUTES",
	help="Set service minutes for the quesion with given question_ID, syntax: SMINUTES <QID>",
	brief="Set service minutes for the question with given question_ID."
)
async def set_service_minutes(ctx, question_id, service_minutes : int):
  tutor_discord_id = str(ctx.author.id)
  tutor_discord_name = ctx.author.name

  await ctx.channel.send(f'Set service minutes {service_minutes} for tutor {tutor_discord_name} question {question_id}')
  question = get_question(question_id)
  db_tutor_id = question['tutor_id']
  if (db_tutor_id != tutor_discord_id):
    await ctx.channel.send(f'Service minutes can only be set by tutor himself for question {question_id}')
    return

  update_s = {
    u'service_minutes':service_minutes,
  }
  update_question(question_id, update_s)

  update_tutor_service_minutes(tutor_discord_id, service_minutes)

  v_channel_id = question['v_channel_id']
  t_channel_id = question['t_channel_id']
  if (v_channel_id != None):
    await delete_private_channel_by_id(int(v_channel_id))
  if (t_channel_id != None):
    await delete_private_channel_by_id(int(t_channel_id))




@bot.command(
  name="SCORE",
	help="Set score for the quesion with given question_ID, syntax: SCORE <QID>",
	brief="Set score for the question with given question_ID."
)
async def score_question(ctx, question_id, score : int): 

  await ctx.channel.send(f'Set score {score} for the tutor of question {question_id}')
  if (score < 1 or score > 5):
    await ctx.channel.send(f'Invalid score {score}: need to be in range [1-5]')
    return

  question = get_question(question_id)
  db_student_id = question['student_id']
  db_tutor_id = question['tutor_id']

  student_discord_id = str(ctx.author.id)
  if (db_student_id != student_discord_id):
    await ctx.channel.send(f'Score can only be set by student himself for question {question_id}')
    return

  update_s = {
    u'score':score,
  }
  update_question(question_id, update_s)
  
  if (db_tutor_id != None):
    update_tutor_total_scores(str(db_tutor_id), score)


  v_channel_id = question['v_channel_id']
  t_channel_id = question['t_channel_id']
  if (v_channel_id != None):
    await delete_private_channel_by_id(int(v_channel_id))
  if (t_channel_id != None):
    await delete_private_channel_by_id(int(t_channel_id))




@bot.command(
  name="GETQ",
	help="Get questions that match a tutor's expertise and preferences",
	brief="Get questions for a tutor"
)
async def get_matching_questions(ctx):
  tutor_discord_id = str(ctx.author.id)

  db_tutor_id = get_tutor(tutor_discord_id)
  if (db_tutor_id is None):
    await ctx.channel.send('Could not find your record as a veteran, did you sign up for veteran form?')
    return

  await dm_matching_questions_for_tutor(ctx, tutor_discord_id)



@bot.command(
  name="SHOWME",
	help="Show my records",
	brief="Show my records"
)
async def show_my_records(ctx):
  discord_id = str(ctx.author.id)
  await show_my_record_as_tutor(ctx, discord_id)
  await show_my_record_as_student(ctx, discord_id)


@bot.command(
  name="RANK",
	help="Show veteran and fledgling rankings",
	brief="Show veteran and fledgling rankings"
)
async def show_tutor_rankings(ctx):
  discord_id = str(ctx.author.id)
  await dm_tutor_rankings(ctx, discord_id)
  await dm_student_rankings(ctx, discord_id)




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
  #delete_documents_in_collection(Questions_ref, 50)
  show_collection(Questions_ref)


@bot.event
async def on_member_join(member):
  print(member.name, member.id, ', on_member_join: welcome to join Ring-a-Bell Tutoring Server!')
  await member.create_dm()
  await member.dm_channel.send(
    f'Hi {member.name}, {member.id}, welcome to join Ring-a-Bell Tutoring Server!'
  )



@bot.event
async def on_member_update(before, after):
  return 
  # unreachable below
  if (before.name.find('Bot') != -1):
    print('skip Bot on_member_update')
    return
  print('on_member_update before: ', before.name, before.id, before.status, before.roles)
  print('on_member_update after: ', after.name, after.id, after.status, after.roles)
  #status: offline (invisible), online, dnd, idle
  if str(after.status) == "online":
    await after.create_dm()
    await after.dm_channel.send(
      f'Hi {after.name} ({after.id}), welcome to be online on Ring-a-Bell Tutoring server!'
    )


@bot.event 
async def on_voice_state_update(member, before, after):
  #NOTE Private_Channel: on_voice_state_update: channel.name is tutor_id, channel.id is unique.
  oldchan = before.channel
  newchan = after.channel
  if(oldchan is not None):
    print(f'oldchan id={oldchan.id} name={oldchan.name} cat={oldchan.category}')
  if(newchan is not None):
    print(f'newchan id={newchan.id} name={newchan.name} cat={newchan.category}')


  # Start a new tutoring call
  if (newchan is not None and newchan.category.name == 'study_room'):
      member_count = len(newchan.members)
      print(f'{datetime.now()}: {member.name} is joining channel ', end='')
      print(f'id={newchan.id} name={newchan.name} cat={newchan.category}, created_at: {newchan.created_at}, member_count_after_joining={len(newchan.members)}')

      v_channel_id = str(newchan.id)
      update_voice_chan_start_questionDB(v_channel_id, member_count)


  # Disconnecting a tutoring call
  if (oldchan is not None and oldchan.category.name == 'study_room'):
      # user (either student or tutor) is leaving private channel of study_room.
      member_count = len(oldchan.members)
      print(f'{datetime.now()}: {member.name} is leaving channel ', end='')
      print(f'id={oldchan.id} name={oldchan.name} cat={oldchan.category}, created_at: {oldchan.created_at}, member_count_after_leaving={member_count}')

      # the first person leaving will mark session complete
      v_channel_id = str(oldchan.id)
      tutor_discord_id, student_discord_id, session_minutes = update_question_session_complete(v_channel_id)
      if (session_minutes > 0):
        update_tutor_total_session_minutes(tutor_discord_id, session_minutes)
        update_student_total_session_minutes(student_discord_id, session_minutes)




@bot.listen()
async def on_message(message):
  if "tutorial" in message.content.lower():
    # in this case don't respond with the word "Tutorial" or you will call the on_message event recursively
      await message.channel.send('This is what you want http://youtube.com/fazttech')
      await bot.process_commands(message)


print('running bot')

server.server()
bot.run(TOKEN)
