
# TOKEN:  OTIyNzAxNDQ5NTgwOTM3MjY4.YcFSsA.aJ25-lIWH_Nuy3cUC5cJoZ8PLJ4
# https://replit.com/join/clitocuutu-kevinwang36
import discord
import os
import math
#import pynacl
#import dnspython
#import server

from discord.ext import commands
import time
from datetime import datetime
import requests
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
#import random

intents = discord.Intents.default()
intents.members = True   # enable intents.members
intents.presences = True

bell_discord_id = '923314875365744641'
keb_discord_id = '850531886261600276'
kv_discord_id = '742820006831587438'
kt_discord_id = '429757950618238987'
bot_discord_id = '922701449580937268'

all_tutor_subject_set = {''}

# Firestore operations
cred = credentials.Certificate('credentials.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

Students_ref = db.collection(u'Students')
Tutors_ref = db.collection(u'Tutors')
Questions_ref = db.collection(u'Questions')
Logs_ref = db.collection(u'Logs')


def get_quote():
  response = requests.get("https://zenquotes.io/api/random")
  json_data = json.loads(response.text)
  quote = json_data[0]['q'] + " -" + json_data[0]['a']
  return quote


is_debug = False 
def debug_print(msg):
  if (is_debug == True):
    print(msg)


async def log_print(msg):
  print(msg)
  await add_log(msg)


async def add_log(log_message):
  cur_epoch_secs = time.time()
  log_s = {
    u'time':cur_epoch_secs,
    u'msg':log_message,
  }

  logs_ref = Logs_ref.document()
  logs_ref.set(log_s)
  #await show_collection(logs_ref, 'Logs')



async def DBG_add_a_student(name, school, grade, discord_id, discord_name):
  await log_print(f'DBG_add_a_student, name={name}, school={school}, grade={grade}, discord_id={discord_id}, discord_name={discord_name}')
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
  #await show_collection(Students_ref, 'Students')


async def DBG_add_a_tutor(name, school, grade, discord_id, discord_name, tutor_subjects):
  await log_print(f'Add_a_tutor, name={name} school={school} grade={grade} discord_id={discord_id} discord_name={discord_name}')
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
    u'total_service_minutes':0,
    u'total_unquestioned_logins':0,
    u'got_a_match':False,
    u'pickedup_a_question':False,
  }

  req_ref = Tutors_ref.document(discord_id)
  req_ref.set(tutor_s)
  await show_collection(Tutors_ref, 'Tutors')


DBG_CNT = 1
async def show_collection(collection_ref, desc_str=''):
  return

  global DBG_CNT
  debug_print(f'DBG_CNT: show collection: {desc_str}')
  DBG_CNT = DBG_CNT + 1
  docs = collection_ref.stream()
  cnt = 0
  for doc in docs:
    cnt = cnt + 1
    debug_print(f'{cnt}: {doc.id} => {doc.to_dict()}')
  debug_print(f'Total records: {cnt}')


async def match_tutors(student_id, subject):
  # matching_tutors here
  matched_tutor_ids = []
  matched_tutor_names = []
  t_ref = Tutors_ref.where((u'tutor_subjects').lower(), u'array_contains', subject.lower()).stream()
  #t_ref = Tutors_ref.where(u'tutor_subjects',u'array_contains', u'apcs').stream()
  for t in t_ref:
    t_dict = t.to_dict()
    t_subjects = t_dict['tutor_subjects']
    t_discord_id = t_dict['discord_id']
    #t_discord_name = t_dict['discord_name']
    member = await get_member_from_id(bot, t_discord_id)
    t_discord_name = str(member)
    if (student_id == t_discord_id): # found student self, skip
      debug_print(f'Skip student self on matching tutor subjects {t_subjects} discord_id= {t_discord_id}')
      continue
    debug_print(f'Found matching tutoring subjects= {t_subjects} discord_id= {t_discord_id}')
    matched_tutor_ids.append(t_discord_id)
    matched_tutor_names.append(t_discord_name)

  await log_print(f'match_tutors: student_id={student_id}, subject={subject} matched_tutors: {matched_tutor_names} {matched_tutor_ids}')
  return matched_tutor_ids


async def dm_matching_questions_for_tutor(dm_channel, tutor_discord_name, tutor_discord_id):
  await log_print(f'dm_matching_questions_for_tutor: name={tutor_discord_name}, id={tutor_discord_id}')
  #dm = await ctx.author.create_dm()

  t_ref = Tutors_ref.document(tutor_discord_id)
  doc = t_ref.get()
  tutor = doc.to_dict()
  debug_print(f'{doc.id} => {tutor}')
  if (tutor is None):
    return

  cur_epoch_secs = time.time()
  new_matches = 0
  tutor_subjects = tutor['tutor_subjects']
  q_ref = Questions_ref.where(u'status', u'==', u'new').stream() 
  for q in q_ref:
    question = q.to_dict()
    #debug_print(f'Found question: {question}')
    q_subject = question['subject']
    student_member = None
    if (q_subject in tutor_subjects):
      new_matches = new_matches + 1
      q_id = question['question_id']
      student_discord_id = question['student_id']
      student_member = await get_member_from_id(bot, student_discord_id)
      q_message = question['message']
      q_images = question['images']
      q_secs = question['question_time']
      q_expire_hours = question['expire_hours']
      q_expire_secs = float(q_expire_hours) * 3600.0
      if (q_expire_secs > 0 and (cur_epoch_secs - q_secs > q_expire_secs)): # question expired
        await log_print(f'Found expired question {q_id} from {str(student_member)} {student_discord_id} raised at {q_secs}, expire=  {q_expire_hours} hours')
        continue

      q_time = time.asctime(time.localtime(q_secs))
      dm_msg = f'Found a matching question from {str(student_member)} raised at {q_time}: {q_subject} {q_message}, question ID={q_id}'
      await log_print(dm_msg)
      await dm_channel.send(dm_msg)
      for img_url in q_images:
        await dm_channel.send(img_url)


  await log_print(f'name={tutor_discord_name}, id={tutor_discord_id}, total new matches={new_matches}')
  if (new_matches == 0):
      dm_msg = f'Have not found unassigned matching questions at present.'
      await dm_channel.send(dm_msg)
  else:
    await update_tutor_total_matches(tutor_discord_name, tutor_discord_id, new_matches)



async def dm_tutor_rankings(ctx, my_discord_id):
  my_discord_name = str(ctx.author)
  await log_print(f'==dm_tutor_rankings: {my_discord_id} {my_discord_name}')
  #dm = await ctx.author.create_dm()
  dm = ctx.channel

  query = Tutors_ref.order_by(u'total_scores', direction=firestore.Query.DESCENDING).limit(50)
  docs = query.stream()
  dm_msg = 'Veteran:\n'
  dm_msg += 'Rank    Score      Veteran Discord ID                  Veteran Discord Name'
  debug_print(dm_msg)
  await dm.send(dm_msg)
  rank = 0
  for doc in docs:
    rank = rank + 1
    debug_print(f': {doc.id} => {doc.to_dict()}')
    tutor = doc.to_dict()
    score = tutor['total_scores']
    tutor_discord_id = tutor['discord_id']
    #tutor_discord_name = tutor['discord_name']
    member = await get_member_from_id(bot, tutor_discord_id)
    tutor_discord_name = str(member)
    dm_msg = f'{rank}:           {score}          {tutor_discord_id}              {tutor_discord_name}'
    if (tutor_discord_id == my_discord_id):
      dm_msg += ' ***'
    debug_print(dm_msg)
    await dm.send(dm_msg)



async def dm_student_rankings(ctx, my_discord_id):
  my_discord_name = str(ctx.author)
  await log_print(f'==dm_student_rankings: {my_discord_id}, {my_discord_name}')
  #dm = await ctx.author.create_dm()
  dm = ctx.channel

  query = Students_ref.order_by(u'total_scores_badges', direction=firestore.Query.DESCENDING).limit(50)
  docs = query.stream()
  dm_msg = 'Fledgling:\n'
  dm_msg += 'Rank    Score      Fledgling Discord ID                Fledgling Discord Name'
  debug_print(dm_msg)
  await dm.send(dm_msg)
  rank = 0
  for doc in docs:
    rank = rank + 1
    debug_print(f': {doc.id} => {doc.to_dict()}')
    student = doc.to_dict()
    score = student['total_scores_badges']
    student_discord_id = student['discord_id']
    #student_discord_name = student['discord_name']
    member = await get_member_from_id(bot, student_discord_id)
    student_discord_name = str(member)

    dm_msg = f'{rank}:           {score}           {student_discord_id}             {student_discord_name}'
    if (student_discord_id == my_discord_id):
      dm_msg += ' ***'
    debug_print(dm_msg)
    await dm.send(dm_msg)



async def show_my_record_as_tutor(ctx, discord_id):
  await log_print(f'==show_my_record_as_tutor: {discord_id}')
  discord_name = str(ctx.author)
  #discord_name = ctx.author.name
  #dm = await ctx.author.create_dm()
  dm = ctx.channel

  t_ref = Tutors_ref.document(discord_id)
  doc = t_ref.get()
  tutor = doc.to_dict()
  if (tutor == None):
    #dm_msg = f'No veteran history for {discord_id} {discord_name}'
    dm_msg = f'No veteran history for {discord_name}'
    debug_print(dm_msg)
    await dm.send(dm_msg)
    return

  debug_print(f'{doc.id} => {tutor}')

  dm_msg = 'Veteran history for ' + discord_name + ':\n'
  dm_msg += 'Total score: ' + str(tutor['total_scores']) + '\n' 
  dm_msg += 'Total matches: ' + str(tutor['total_matches']) + '\n' 
  dm_msg += 'Total pickups: ' + str(tutor['total_pickups']) + '\n' 
  await dm.send(dm_msg)
  dm_msg = ''
  dm_msg += 'Total sessions: ' + str(tutor['total_sessions']) + '\n' 
  dm_msg += 'Total session minutes: ' + str(tutor['total_session_minutes']) + '\n' 
  dm_msg += 'Total service minutes: ' + str(tutor['total_service_minutes']) + '\n\n' 
  await dm.send(dm_msg)


async def show_my_record_as_student(ctx, discord_id):
  await log_print(f'==show_my_record_as_student: {discord_id}')
  discord_name = str(ctx.author)
  #discord_name = ctx.author.name
  #dm = await ctx.author.create_dm()
  dm = ctx.channel

  s_ref = Students_ref.document(discord_id)
  doc = s_ref.get()
  student = doc.to_dict()
  if (student == None):
    #dm_msg = f'No fledgling history for {discord_id} {discord_name}'
    dm_msg = f'No fledgling history for {discord_name}'
    debug_print(dm_msg)
    await dm.send(dm_msg)
    return

  debug_print(f'{doc.id} => {student}')

  total_unanswered_questions = student['total_questions'] - student['total_sessions']

  dm_msg = 'Fledgling history for ' + discord_name + ':\n'
  dm_msg += 'Total questions: ' + str(student['total_questions']) + '\n' 
  dm_msg += 'Total sessions: ' + str(student['total_sessions']) + '\n' 
  await dm.send(dm_msg)
  dm_msg = ''
  dm_msg += 'Total session minutes: ' + str(student['total_session_minutes']) + '\n' 
  dm_msg += 'Total unanswered questions: ' + str(total_unanswered_questions) + '\n' 
  dm_msg += 'Total scores and badges: ' + str(student['total_scores_badges']) + '\n\n' 
  #dm_msg += 'Total wait minutes: ' + str(student['total_wait_minutes']) + '\n\n' 
  await dm.send(dm_msg)


async def get_one_tutor_subjects(tutor_discord_id):
  # show one tutor's subjects
  t_ref = Tutors_ref.document(tutor_discord_id)
  tutor = t_ref.to_dict()
  if (tutor is None):
    debug_print(f'No veteran record for {tutor_discord_id}')
    return None

  tutor_subjects = tutor['tutor_subjects']
  return tutor_subjects


async def get_all_tutor_subjects():
  # show all of tutors subjects (unique)
  subject_set = set()
  t_ref = Tutors_ref.stream()
  for t in t_ref:
    tutor = t.to_dict()
    if (tutor is None):
      return subject_set

    tutor_subjects = tutor['tutor_subjects']
    #tutor_id = tutor['discord_id']
    #debug_print(f'tutor_id: {tutor_id}, tutor_subjects {tutor_subjects}')
    for one_subject in tutor_subjects:
      subject_set.add(one_subject)

  debug_print(f'In get_all_tutor_sujects: subject_set = {subject_set}')
  return subject_set


async def delete_documents_in_collection(collection_ref, batch_size):
  debug_print(f'In delete_documents_in_collection:')
  docs = collection_ref.limit(batch_size).stream()
  deleted = 0
  for doc in docs:
    debug_print(f'{deleted+1}: deleting doc {doc.id} => {doc.to_dict()}')
    doc.reference.delete()
    deleted = deleted + 1



async def DBG_initialization():
  if (True):
    delete_documents_in_collection(Students_ref, 10)
    delete_documents_in_collection(Tutors_ref, 10)
    DBG_add_a_student("fledgling_a", "Sun1", 5, keb_discord_id, "keb#0598")
    DBG_add_a_student("fledgling_b", "Sun2", 8, kt_discord_id, "kaitlynッ#2666")
    DBG_add_a_student("fledgling_c", "Sun3", 5, bell_discord_id, "bell_#6316")
    tutor_subjects=[]
    tutor_subjects.append('english')
    tutor_subjects.append('math')
    debug_print(tutor_subjects)
    DBG_add_a_tutor("veteran_x", "Sun4", 10, kv_discord_id, "Kevin Wang#8725", tutor_subjects)
    DBG_add_a_tutor("veteran_z", "Sun3", 10, kt_discord_id, "kaitlynッ#2666", ['spanish'])
    DBG_add_a_tutor("veteran_y", "Sun3", 10, bell_discord_id, "bell_#6316", tutor_subjects)

    delete_documents_in_collection(Questions_ref, 10)
    show_collection(Questions_ref, 'Questions')

  await show_collection(Tutors_ref, 'Tutors')
  matched_tutors = await match_tutors("test_user_id", "english")
  return matched_tutors





async def update_tutor(tutor_discord_id, update_s):
  debug_print(f'==update_tutor: {tutor_discord_id} {update_s}')
  t_ref = Tutors_ref.document(tutor_discord_id)
  t_ref.update(update_s)
  await show_collection(Tutors_ref, 'Tutors')


async def update_tutor_service_minutes(discord_id, discord_name, service_minutes):
  await log_print(f'update_tutor_service_minutes: veteran {discord_id} {discord_name} {service_minutes}')
  t_ref = Tutors_ref.document(discord_id)
  doc = t_ref.get()
  debug_print(f'{doc.id} => {doc.to_dict()}')
  tutor = doc.to_dict()
  total_service_minutes = tutor['total_service_minutes']
  debug_print(f'total_service_minutes = {total_service_minutes}')

  new_total_service_minutes = total_service_minutes + service_minutes

  #debug_print(f'tutor: {discord_name} {discord_id} old total_service_minutes={total_service_minutes}, new total_service_minutes={new_total_service_minutes}')
  update_s = {
    u'total_service_minutes':new_total_service_minutes,
    u'discord_name':discord_name
  }
  t_ref.update(update_s)
  await show_collection(Tutors_ref, 'Tutors')


async def update_tutor_total_scores(discord_id, score):
  await log_print(f'==update_tutor_total_scores: discord_id={discord_id}, score={score}')
  t_ref = Tutors_ref.document(discord_id)
  doc = t_ref.get()
  debug_print(f'{doc.id} => {doc.to_dict()}')
  tutor = doc.to_dict()
  total_scores = tutor['total_scores']
  #discord_name = tutor['discord_name']
  member = await get_member_from_id(bot, discord_id)
  discord_name = str(member)

  new_total_scores = total_scores + score

  debug_print(f'veteran: {discord_name} {discord_id} old total_scores={score}, new total_scores={new_total_scores}')
  update_s = {
    u'total_scores':new_total_scores,
    u'discord_name':discord_name
  }
  t_ref.update(update_s)
  await show_collection(Tutors_ref, 'Tutors')


async def update_tutor_total_pickups(discord_name, discord_id):
  t_ref = Tutors_ref.document(discord_id)
  doc = t_ref.get()
  debug_print(f'{doc.id} => {doc.to_dict()}')
  tutor = doc.to_dict()
  total_pickups = tutor['total_pickups']
  new_total_pickups = total_pickups + 1

  await log_print(f'update_tutor_total_pickups: {discord_name} {discord_id} prev {total_pickups}, new {new_total_pickups}')
  update_s = {
    u'total_pickups':new_total_pickups,
    u'pickedup_a_question':True,
    u'discord_name':discord_name
  }
  t_ref.update(update_s)
  await show_collection(Tutors_ref, 'Tutors')




async def update_tutor_total_matches(discord_name, discord_id, new_matches=1):
  t_ref = Tutors_ref.document(discord_id)
  doc = t_ref.get()
  debug_print(f'{doc.id} => {doc.to_dict()}')
  tutor = doc.to_dict()
  total_matches = tutor['total_matches']
  new_total_matches = total_matches + new_matches

  await log_print(f'update_tutor_total_matches: {discord_name} {discord_id} prev={total_matches}, new={new_total_matches}')
  update_s = {
    u'total_matches':new_total_matches,
    u'got_a_match':True,
    u'discord_name':discord_name
  }
  t_ref.update(update_s)
  await show_collection(Tutors_ref, 'Tutors')


async def add_question(question_id, student_id, subject, expire_hours, question_text, img_urls):
  epoch_secs = time.time()
  debug_print(f'==add_question: {epoch_secs} {question_id} {student_id}, {subject}, {expire_hours}, {question_text}, {img_urls}')
  
  question_s = {
    u'status':u'new',
    u'question_id':question_id,
    u'v_channel_id':'',
    u't_channel_id':'',
    u'student_id':student_id,
    u'tutor_id':'',
    u'subject':subject,
    u'extra_info':'',
    u'message':question_text,
    u'images':img_urls,
    u'question_time':epoch_secs,
    u'expire_hours':0,
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
  await show_collection(Questions_ref, 'Questions')


async def get_question_tutor_and_student_id(question_id):
  debug_print(f'====get_question_tutor_and_student_id: {question_id}')
  q_ref = Questions_ref.document(question_id)
  doc = q_ref.get()    
  question = doc.to_dict()
  if (question == None):
    return None, None

  student_discord_id = question['student_id']
  tutor_discord_id = question['tutor_id']
  debug_print(f'question {question_id}: student={student_discord_id} tutor={tutor_discord_id}')
  return student_discord_id, tutor_discord_id


async def update_discord_name(discord_id, new_discord_name):
  s_ref = Students_ref.document(discord_id)
  doc = s_ref.get()
  debug_print(f'{doc.id} => {doc.to_dict()}')
  student = doc.to_dict()
  if (student is None):
    debug_print(f'update_discord_name: no fledgling record found for {discord_id}')
  else:
    prev_discord_name = student['discord_name']
    await log_print(f'update_student_discord_name: {discord_id} prev={prev_discord_name}, new={new_discord_name}')
    update_s = {
      u'discord_name':new_discord_name,
    }
    s_ref.update(update_s)  
    await show_collection(Students_ref, 'Students')

  t_ref = Tutors_ref.document(discord_id)
  doc = t_ref.get()
  debug_print(f'{doc.id} => {doc.to_dict()}')
  tutor = doc.to_dict()
  if (tutor is None):
    debug_print(f'update_discord_name: no veteran record found for {discord_id}')
  else:
    prev_discord_name = tutor['discord_name']
    await log_print(f'update_student_discord_name: {discord_id} prev={prev_discord_name}, new={new_discord_name}')
    update_s = {
      u'discord_name':new_discord_name,
    }
    t_ref.update(update_s)  
    await show_collection(Tutors_ref, 'Tutors')
  




async def update_student_total_questions(discord_id, discord_name):
  s_ref = Students_ref.document(discord_id)
  doc = s_ref.get()
  debug_print(f'{doc.id} => {doc.to_dict()}')
  student = doc.to_dict()
  if (student is None):
    debug_print(f'upate_student_total_questions: no fledgling record found for {discord_id}')
    return

  total_questions = student['total_questions']
  new_total_questions = total_questions + 1
  new_total_scores_badges = new_total_questions

  await log_print(f'update_student_total_q: {discord_id} prev={total_questions}, new={new_total_questions}')
  update_s = {
    u'total_questions':new_total_questions,
    u'total_scores_badges':new_total_scores_badges,
    u'discord_name':discord_name
  }
  s_ref.update(update_s)
  await show_collection(Students_ref, 'Students')



async def update_student_total_wait_minutes(discord_id, wait_minutes):
  s_ref = Students_ref.document(discord_id)
  doc = s_ref.get()
  debug_print(f'{doc.id} => {doc.to_dict()}')
  student = doc.to_dict()
  if (student is None):
    debug_print(f'update_student_total_wait_minutes: no fledgling record found for {discord_id}')
    return

  total_wait_minutes = student['total_wait_minutes']
  new_total_wait_minutes = total_wait_minutes + wait_minutes

  await log_print(f'update_student_total_wait: {discord_id} old={wait_minutes}, new={new_total_wait_minutes}')
  update_s = {
    u'total_wait_minutes':new_total_wait_minutes
  }
  s_ref.update(update_s)
  await show_collection(Students_ref, 'Students')


# Update total_sessions, total_session_minutes for the student
async def update_student_total_session_minutes(discord_id, session_minutes):
    s_ref = Students_ref.document(discord_id)
    doc = s_ref.get()
    debug_print(f'{doc.id} => {doc.to_dict()}')
    student = doc.to_dict()
    if (student is None):
      debug_print(f'update_student_total_session_minutes: no fledgling record found for {discord_id}')
      return
  
    total_sessions = student['total_sessions']
    total_session_minutes = student['total_session_minutes']
    new_total_sessions = total_sessions + 1
    new_total_session_minutes = total_session_minutes + session_minutes
    await log_print(f'update_student: {discord_id} new total_sessions={new_total_sessions}, total_session_minutes={new_total_session_minutes}')

    update_s = {
      u'total_sessions':new_total_sessions,
      u'total_session_minutes':new_total_session_minutes
    }
    Students_ref.document(doc.id).update(update_s)
    await show_collection(Students_ref, 'Students')


async def update_question(question_id, update_s):
  debug_print(f'==update_question: {question_id} {update_s}')
  q_ref = Questions_ref.document(question_id)
  doc = q_ref.get()    
  question = doc.to_dict()
  if (question == None):
    debug_print(f'No question found with question_id {question_id}')
    return None, None

  v_channel_id = question['v_channel_id']
  t_channel_id = question['t_channel_id']
  student_id = question['student_id']
  tutor_id = question['tutor_id']

  q_ref.update(update_s)
  await show_collection(Questions_ref, 'Questions')
  return tutor_id, student_id, v_channel_id, t_channel_id




async def update_voice_chan_start_questionDB(v_chan_id, member_count):
  new_status = 'session-start-' + str(member_count)
  epoch_secs = time.time()
  update_s = {
    u'status':new_status,
    u'session_start_time':epoch_secs,
  }
  debug_print(f'==update_voice_chan_start_questionDB, v_chan_id= {v_chan_id}, member_count= {member_count}, update_s={update_s}')
  q_ref = Questions_ref.where(u'v_channel_id', u'==', v_chan_id)
  docs = q_ref.get()
  for doc in docs:
    debug_print(f'{doc.id} => {doc.to_dict()}')
    question = doc.to_dict()
    if (question == None):
      debug_print(f'No question found with voice channel id {v_chan_id}')
      return

    status = question['status']
    t_chan_id = question['t_channel_id']
    debug_print(f'question old status = {status}, v_channel_id={v_chan_id}, t_channel_id={t_chan_id} new status = {new_status}')
    Questions_ref.document(doc.id).update(update_s)
    await show_collection(Questions_ref, 'Questions')
    await log_print(f'update_voice_chan_start: vchan={v_chan_id}, tchan={t_chan_id}, mc={member_count}, old={status}, update_s={update_s}')




async def update_question_session_complete(v_chan_id):
  debug_print(f'==update_question_session_complete: v_channel_id= {v_chan_id}')
  session_complete_time = time.time()
  q_ref = Questions_ref.where(u'v_channel_id', u'==', v_chan_id)
  docs = q_ref.get()
  debug_print(f'== docs == {docs}')
  if (docs == []):
    await log_print(f'Err: no question found with voice channel id {v_chan_id}')
    return None, None, 0

  for doc in docs:
    debug_print(f'{doc.id} => {doc.to_dict()}')
    question = doc.to_dict()
    if (question == None):
      await log_print(f'Err: no question found with voice channel id {v_chan_id}')
      return None, None, 0

    old_status = question['status']
    tutor_discord_id = question['tutor_id']
    student_discord_id = question['student_id']
    old_session_minutes = question['session_minutes']
    debug_print(f'question old_status = {old_status}')

    if (old_status == 'session-start-2'):
      # a good session with 2 people joined, mark session-complete
      new_status = 'session-complete'
      debug_print(f'(complete session) question status: old = {old_status}, new = {new_status}')
    else: # could be: new picked-up, session-start-1
      # keep question status unchanged so we know where it was left. (more informational than setting session-incomplete)
      await log_print(f'update_q_session_complete: (incomplete session) status={old_status}, no update')
      return tutor_discord_id, student_discord_id, 0

    session_start_time = question['session_start_time']
    session_minutes = round((session_complete_time - session_start_time) / 60.0, 2)
    accumulated_session_minutes = old_session_minutes + session_minutes
    msg = (f'session_start_time={time.asctime(time.localtime(session_start_time))}')
    msg += ' ' + (f'session_complete_time={time.asctime(time.localtime(session_complete_time))}')
    msg += ' ' + (f'session_minutes old={old_session_minutes}, new={session_minutes}')
    msg += ' ' + (f'new_status {new_status}, total_session_minutes={accumulated_session_minutes}')
    await log_print(msg)

    update_s = {
      u'status':new_status,
      u'session_complete_time':session_complete_time,
      u'session_minutes':accumulated_session_minutes,
    }
    Questions_ref.document(doc.id).update(update_s)
    await show_collection(Questions_ref, 'Questions')
    return tutor_discord_id, student_discord_id, session_minutes


async def update_tutor_total_session_minutes(discord_id, session_minutes):
    # Update total_sessions, total_session_minutes for the tutor
    t_ref = Tutors_ref.document(discord_id)
    doc = t_ref.get()
    debug_print(f'{doc.id} => {doc.to_dict()}')
    tutor = doc.to_dict()
    if (tutor == None):
      debug_print(f'No tutor found with discord id {discord_id}')
      return

    total_sessions = tutor['total_sessions']
    #discord_name = tutor['discord_name']
    total_session_minutes = tutor['total_session_minutes']
    new_total_sessions = total_sessions + 1
    new_total_session_minutes = total_session_minutes + session_minutes
    await log_print(f'update_tutor_t_session_minutes: {discord_id} new t_sessions={new_total_sessions}, t_session_minutes={new_total_session_minutes}')

    update_s = {
      u'total_sessions':new_total_sessions,
      u'total_session_minutes':new_total_session_minutes
    }
    Tutors_ref.document(doc.id).update(update_s)
    await show_collection(Tutors_ref, 'Tutors')



async def get_question(question_id):
  question = Questions_ref.document(question_id).get().to_dict()
  debug_print(f'==get_question: question_id= {question_id} question= {question}')
  return question

async def get_student(student_discord_id):
  student = Students_ref.document(student_discord_id).get().to_dict()
  debug_print(f'==get_student: student_question_id= {student_discord_id}, student={student}')
  return student

async def get_tutor(tutor_discord_id):
  tutor = Tutors_ref.document(tutor_discord_id).get().to_dict()
  debug_print(f'==get_tutor: tutor_question_id= {tutor_discord_id}, student={tutor}')
  return tutor



#async def get_member_from_id_ctx(ctx: commands.Context, discord_id):
#all_members = ctx.bot.get_all_members()
async def get_member_from_id(bot, discord_id):
  debug_print(f'In get_member_from_id, looking for {discord_id}')
  all_members = bot.get_all_members()
  for member in all_members:
    debug_print(f'{str(member)}, {member.id}')
    if (str(member.id) == discord_id):
      debug_print(f'found member {discord_id}, {str(member)}')
      return member
  return None



async def create_private_channel(guild, question_id, student_id, tutor_id): 
  debug_print(f'create_private_channel: question_id={question_id}, tutor={tutor_id}, student={student_id}')

  tutor_member = await get_member_from_id(bot, tutor_id)
  student_member = await get_member_from_id(bot, student_id)
  if (False):
    invitelink = 'test invite link'
    debug_print(f'private channel: student_member: {str(student_member)} {student_member.id}')
    await student_member.create_dm()
    await student_member.dm_channel.send(invitelink)
    debug_print(f'private channel: tutor_member: {str(tutor_member)} {tutor_member.id}')
    await tutor_member.create_dm()
    await tutor_member.dm_channel.send(invitelink)

  category_name = "private_tutoring_rooms"
  category = discord.utils.get(guild.categories, name=category_name)
  #user = ctx.author.id
  category_overwrites = {
    guild.default_role: discord.PermissionOverwrite(read_messages=False),
    guild.me: discord.PermissionOverwrite(read_messages=True),
    #ctx.author: discord.PermissionOverwrite(read_messages=True),
    student_member: discord.PermissionOverwrite(read_messages=True),
    tutor_member: discord.PermissionOverwrite(read_messages=True)}

  channel_overwrites = {
    guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False),
    #guild.me: discord.PermissionOverwrite(read_messages=True),
    student_member: discord.PermissionOverwrite(read_messages=True),
    tutor_member: discord.PermissionOverwrite(read_messages=True)}


  if category is None: #If there's no category matching with the `name`
    await log_print(f'creating private channels category {category_name}')
    category = await guild.create_category(category_name, overwrites=category_overwrites, reason=None)
    if (category is None):
      await log_print('Err: category is None after create_category')


  t_chan_name = 'text_' + str(question_id)
  v_chan_name = 'voice_' + str(question_id)

  await log_print(f'create private channels: student: {str(student_member)}, {student_member.id} -- tutor: {str(tutor_member)}, {tutor_member.id}, t_chan_name {t_chan_name} v_chan_name {v_chan_name}')

  t_chan = await guild.create_text_channel(t_chan_name, overwrites=channel_overwrites, reason=None, category=category)
  t_invitelink = await t_chan.create_invite(max_uses=1,unique=True)
  msg = (f'priv_text_chan id= {t_chan.id}, name={t_chan.name}, link={t_invitelink} \n')

  v_chan = await guild.create_voice_channel(v_chan_name, overwrites=channel_overwrites, reason=None, category=category)
  v_invitelink = await v_chan.create_invite(max_uses=1,unique=True)
  msg += (f'priv_voice_chan id= {v_chan.id}, name={v_chan.name}, link={v_invitelink}')
  await log_print(msg)

  await student_member.create_dm()
  await tutor_member.create_dm()

  dm_msg = f'Hi veteran {str(tutor_member)} and fledgling {str(student_member)}! Please join your private voice channel and text channel to start your private tutoring session.'
  await student_member.dm_channel.send(dm_msg)
  await tutor_member.dm_channel.send(dm_msg)

  await student_member.dm_channel.send(v_invitelink)
  await tutor_member.dm_channel.send(v_invitelink)
  
  await student_member.dm_channel.send(t_invitelink)
  await tutor_member.dm_channel.send(t_invitelink)
  
  return v_chan.id, t_chan.id


async def delete_private_channel_by_id(channel_id):
  private_chan = bot.get_channel(int(channel_id))
  debug_print(f'channel_id = {channel_id}, private_chan = {private_chan}')
  if (private_chan == None):
    await log_print(f'delete_chan err: did not find channel_id = {channel_id}, private_chan = {private_chan}')
    return

  member_count = len(private_chan.members)
  #if (member_count == 0):
  if (True):
    await log_print(f'deleting pivate_channel name {private_chan.name}, id={private_chan.id}, created_at: {private_chan.created_at}, member_count={member_count}')
    await private_chan.delete()





bot = commands.Bot(command_prefix="!", intents=intents)
TOKEN = os.getenv("DISCORD_TOKEN")



@bot.command(pass_context=True,
  name="RING",
	help="Asks a question: RING sub=<subjects> expire=<expire_hours> <question text> <question image>. A unique question ID will be generated. Question will expire after <expire_hours>.",
	brief="Asks a question sub=<subjects> expire=<hours> <question txt> <img> => question ID"
)
#async def ask_question(ctx, *args):
async def ask_question(ctx, subject_text:str, expire_text:str, *args):
  student_discord_id = str(ctx.author.id)
  student_discord_name = str(ctx.author)
  debug_print(f'ask_question: student {student_discord_id} {student_discord_name}: {subject_text}, {expire_text}, {args}')

  if ((subject_text.find("sub=") == -1) or (expire_text.find("expire=") == -1)):
    msg1 = (f'Hi {student_discord_name}! Please retry with following format to ask a question (run help RING for more info):')
    await ctx.channel.send(msg1)
    msg2 = (f'RING sub=<subjects> expire=<expire_hours> <question text> <uploaded image>')
    await ctx.channel.send(msg2)
    await log_print(msg1 + ' ' + msg2)
    return

  db_student_id = await get_student(str(student_discord_id))
  if (db_student_id is None):
    msg = 'Hi {student_discord_name}: could not find you as a fledgling, please first sign up the fledgling form at https://ringabell.webflow.io/'
    await ctx.channel.send(msg)
    await log_print(msg)
    return


  question_attach = ctx.message.attachments
  #message_text = ctx.message.content
  #subject_text = message_text.split(" ")[1]
  #subject = subject_text.split("=")[1]
  #expire_text = message_text.split(" ")[2]
  subject = subject_text.split("=")[1]
  debug_print(f'subject_text {subject_text}, subject={subject}')

  found_subject = False
  for s in all_tutor_subject_set:
    if (s == subject):
      found_subject = True
      break
  if (found_subject == False):
    msg = (f'Unknown subject {subject}, all tutoring subjects are: {all_tutor_subject_set}. please retry')
    await ctx.channel.send(msg)
    await log_print(msg)
    return


  expire_hours = expire_text.split("=")[1]
  debug_print(f'expire: {expire_text}, expire_hours={expire_hours}')
  if (expire_hours.isnumeric() == False):
    msg = (f'Hi {student_discord_name}! I am confused by {expire_text}. Please retry with expiration time being a number in hours.')
    await ctx.channel.send(msg)
    await log_print(msg)
    return

  expire_hours = round(float(expire_hours), 2)
  question_response = f'Got it! Question subject: {subject}. Question will expire after {expire_hours} hours'
  await ctx.channel.send(question_response)

  #extra_text = message_text.split(" ")[3:]
  question_text = ''
  for extra in args:
    question_text += extra + ' '

  img_urls = []
  num_att = len(question_attach)
  num_img = 0
  for idx in range(num_att):
    attach_url_str = str(question_attach[idx].url)
    debug_print(f'attach_url_str = {attach_url_str}')
    if (attach_url_str.startswith('http')):
      img_urls.append(attach_url_str)
      num_img += 1


  #question_id = student_discord_name + '.' + str(time.time())
  #question_id = student_discord_id + '.' + str(time.time())
  question_id = str(math.floor(time.time()))
  question_response = f'Received your question from {student_discord_name}: generated question ID = {question_id}\n'
  msg = f'Received your question and sent to all available tutors! For reference, here is your question ID which you can use for feedback and scoring after the session: {question_id}\n'
  await ctx.channel.send(msg)
  await log_print(f'question_id={question_id} s={subject}, e={expire_hours}, q={question_text}, natt {num_att}, nimg {num_img} imgurls = {img_urls}')


  await add_question(question_id, student_discord_id, subject, expire_hours, question_text, img_urls)
  await update_student_total_questions(student_discord_id, student_discord_name)

  # return tutor discord_ids
  matched_tutor_ids = await match_tutors(student_discord_id, subject)
  debug_print(f'matched_tutors returned: {matched_tutor_ids}')
  for tutor_discord_id in matched_tutor_ids:
    # status: offline (invisible), online, dnd, idle
    # skip tutors in offline(invisible) and 'dnd' status (idle is ok)
    member = await get_member_from_id(ctx.bot, tutor_discord_id)
    discord_status = str(member.status)
    if (discord_status != "online" and discord_status != "idle"):
      log_print(f'skip veteran {str(member)} {tutor_discord_id} in status ({discord_status})')
      continue

    await member.create_dm()
    match_msg = f'Hi {str(member)}, you are matched to question_id {question_id}:'
    await member.dm_channel.send(match_msg)
    subject_msg = f'Subject: {subject}'
    await member.dm_channel.send(subject_msg)
    question_msg = f'Question: {question_text}'
    await member.dm_channel.send(question_msg)
    for img_url in img_urls:
      await member.dm_channel.send(img_url)

    await log_print(f'{str(member)} {member.id}: matched to question_id {question_id}')

    await update_tutor_total_matches(str(member), tutor_discord_id)




@bot.command(
  name="PICKUP",
	help="Picks up a quesion with a given question ID, syntax: PICKUP <Question ID>",
	brief="Picks up a question with a given question ID"
)
async def answer_question(ctx, question_id): 
  tutor_discord_id_str = str(ctx.author.id)
  tutor_discord_name = str(ctx.author)
  msg = (f'Picking up question {question_id} from veteran {tutor_discord_name} {tutor_discord_id_str}')
  await log_print(msg)

  question = await get_question(question_id)
  if (question['student_id'] == tutor_discord_id_str):
    msg = (f'Hi {tutor_discord_name}! Did you want to pick up your own question {question_id}? LOL!')
    await ctx.channel.send(msg)
    return

  if (question['status'] != 'new'):
    msg = (f'Question {question_id} has been picked up by another veteran')
    await ctx.channel.send(msg)
    await log_print(msg)
    return

  # Update question DB first to prevent conflict (another tutor may be doing it at the same time)
  pickup_time = time.time()
  update_s = {
    u'status':u'picked-up',
    u'tutor_id':tutor_discord_id_str,
    u'picked_up_time':pickup_time,
  }
  await update_question(question_id, update_s)

  question = await get_question(question_id)
  if (question['status'] != 'picked-up' or question['tutor_id'] != tutor_discord_id_str):
    # another tutor took it before me. Give up
    msg = (f'Question {question_id} has been picked up by another veteran')
    await ctx.channel.send(msg)
    await log_print(msg)
    return


  msg = (f'Hi {tutor_discord_name}! It is great to pick up question {question_id}!')
  await ctx.channel.send(msg)

  student_discord_id_str = question['student_id']
  question_time = question['question_time']
  wait_minutes = round((pickup_time - question_time) / 60.0, 2)

  for guild in bot.guilds:
    debug_print(f'bot.guild={guild} bot.guild.id={guild.id}')    #Ring a Bell, #922560105650733066
    #student_discord_id = keb_discord_id
    #tutor_id =   kv_discord_id
    v_chan_id, t_chan_id = await create_private_channel(guild, question_id, student_discord_id_str, tutor_discord_id_str)
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
  await update_question(question_id, update_s)
  ## TODO: transaction
  await update_tutor_total_pickups(tutor_discord_name, tutor_discord_id_str)
  await update_student_total_wait_minutes(student_discord_id_str, wait_minutes)


  


@bot.command(
  name="SMINUTES",
	help="Sets service minutes for a quesion with a given question ID, syntax: SMINUTES <Question ID> <minutes> (<feedback message>)",
	brief="Sets service minutes for a question with feedack message"
)
async def set_service_minutes(ctx, question_id, service_minutes : int, *args):
  tutor_discord_id = str(ctx.author.id)
  tutor_discord_name = str(ctx.author)

  send_msg = f'Hi {tutor_discord_name}! Thanks for providing service minutes {service_minutes} for question ID {question_id}'
  log_msg = send_msg + ' ' + (f'args={args}')
  await ctx.channel.send(send_msg)
  await log_print(log_msg)
  
  question = await get_question(question_id)
  db_tutor_id = question['tutor_id']
  if (db_tutor_id != tutor_discord_id):
    msg = (f'Sorry! Service minutes can only be set by the veteran who tutored question {question_id}')
    await ctx.channel.send(msg)
    await log_print(msg)
    return

  feedback=''
  for a in args:
    feedback += a + ' '
  await ctx.channel.send(f'Feedback: {feedback}')

  v_channel_id = question['v_channel_id']
  t_channel_id = question['t_channel_id']
  if (v_channel_id != None):
    await delete_private_channel_by_id(int(v_channel_id))
  if (t_channel_id != None):
    await delete_private_channel_by_id(int(t_channel_id))


  update_s = {
    u'service_minutes':service_minutes,
    u'tutor_feedback':feedback,
  }
  await update_question(question_id, update_s)

  await update_tutor_service_minutes(tutor_discord_id, tutor_discord_name, service_minutes)





@bot.command(
  name="SCORE",
	help="Sets score for a quesion with a given question ID, syntax: SCORE <question ID> <score> (<feedback message>)",
	brief="Sets score for a question with feedback message"
)
async def score_question(ctx, question_id, score : int, *args): 
  student_discord_id = str(ctx.author.id)
  student_discord_name = str(ctx.author)

  send_msg = f'Hi {student_discord_name}! Thanks for providing score {score} for question ID {question_id}'
  await ctx.channel.send(send_msg)
  log_msg = send_msg + ' ' + (f'args={args}')
  await log_print(log_msg)

  if (score < 1 or score > 5):
    msg = (f'Hi {student_discord_name}! Provided score was {score}: The range of score needs to be in range [1-5]. Try again!')
    await ctx.channel.send(msg)
    await log_print(msg)
    return

  feedback=''
  for a in args:
    feedback += a + ' '

  await ctx.channel.send(f'Feedback: {feedback}')
  
  question = await get_question(question_id)
  db_student_id = question['student_id']
  db_tutor_id = question['tutor_id']

  if (db_student_id != student_discord_id):
    msg = (f'Score can only be set by fledgling who raised question {question_id}')
    await ctx.channel.send(msg)
    await log_print(msg)
    return

  update_s = {
    u'score':score,
    u'student_feedback':feedback,
  }
  await update_question(question_id, update_s)
  
  if (db_tutor_id != None):
    await update_tutor_total_scores(str(db_tutor_id), score)


  v_channel_id = question['v_channel_id']
  t_channel_id = question['t_channel_id']
  if (v_channel_id != None):
    await delete_private_channel_by_id(int(v_channel_id))
  if (t_channel_id != None):
    await delete_private_channel_by_id(int(t_channel_id))



@bot.command(pass_context=True,
  name="FEEDBACK",
	help="Gives feedback for a quesion with a given question ID, syntax: FEEDBACK <Question ID>",
	brief="Gives feedback for a question with a given question ID"
)
async def set_feedback(ctx, question_id):
  discord_id = str(ctx.author.id)
  discord_name = str(ctx.author)
  feedback_msg = ctx.message.content.split(" ")[2:]

  feedback_text = ''
  for text in feedback_msg:
    feedback_text += text + ' '

  msg = (f'Got feedback for question ID {question_id}: {feedback_text}')
  await ctx.channel.send(msg)
  await log_print(msg)

  question = await get_question(question_id)
  db_tutor_id = question['tutor_id']
  db_student_id = question['student_id']
  if (db_tutor_id == discord_id):
    update_s = {
      u'tutor_feedback':feedback_text,
    }
    await update_question(question_id, update_s)
  else:
    if (db_student_id == discord_id):
      update_s = {
        u'student_feedback':feedback_text,
      }
      await update_question(question_id, update_s)
    else:
      msg = (f'Hi {discord_name}! Feedback can only be set by the veteran or the fledgling for question {question_id}')
      await ctx.channel.send(msg)
      await log_print(msg)
      return



@bot.command(
  name="GETQ",
	help="Gets questions that match a veteran's expertise and preferences",
	brief="Gets matching questions for a veteran"
)
async def get_matching_questions(ctx):
  tutor_discord_id = str(ctx.author.id)
  tutor_discord_name = str(ctx.author)

  db_tutor_id = await get_tutor(tutor_discord_id)
  if (db_tutor_id is None):
    msg = ('Could not find you as a veteran, please first sign up the veteran form at https://ringabell.webflow.io/')
    await ctx.channel.send(msg)
    await log_print(msg)
    return

  await dm_matching_questions_for_tutor(ctx.channel, tutor_discord_name, tutor_discord_id)



@bot.command(
  name="SHOWME",
	help="Shows my records: questions, sessions, etc.",
	brief="Shows my records: questions, sessions, etc."
)
async def show_my_records(ctx):
  discord_id = str(ctx.author.id)
  discord_name = str(ctx.author)
  await show_my_record_as_tutor(ctx, discord_id)
  await show_my_record_as_student(ctx, discord_id)
  msg = (f'showme: {discord_id} {discord_name}')
  await log_print(msg)

@bot.command(
  name="RANK",
	help="Shows veteran and fledgling rankings",
	brief="Shows veteran and fledgling rankings"
)
async def show_tutor_rankings(ctx):
  discord_id = str(ctx.author.id)
  discord_name = str(ctx.author)
  await dm_tutor_rankings(ctx, discord_id)
  await dm_student_rankings(ctx, discord_id)
  msg = (f'rank: {discord_id} {discord_name}')
  await log_print(msg)


@bot.command(
  name="SUBJECTS",
	help="Shows all available tutoring subjects currently provided by veterans",
	brief="Shows all available tutoring subjects"
)
async def show_all_tutor_subjects(ctx):

  all_tutor_subject_set = await get_all_tutor_subjects()

  debug_print(all_tutor_subject_set)
  dm_msg = 'All available tutoring subjects:\n[ '
  for s in all_tutor_subject_set:
    if (s != ''):
      dm_msg += s + '   ';
  dm_msg += ']'

  dm = ctx.channel
  await dm.send(dm_msg)
  log_msg = (f'run by {str(ctx.author)} {ctx.author.id}: {dm_msg}')
  await log_print(log_msg)


#@bot.command(pass_context=True)
#async def sendimage(ctx):
    #await ctx.send('Working!', file=discord.File('./IMG_2266.JPG'))
    #imgList = os.listdir("./images/") # Creates a list of filenames from your folder 
#    imgfile = "./images/IMG_2266.JPG"  # Note: it's stored in repl.it /images/ folder 
#    await ctx.send('Send image:', file=discord.File(imgfile)) # Sends the image in the channel the command was used


@bot.command(
  pass_context=True,
  name="SHOWQ",
  help="Shows pending questions (admin only)",
  brief="Shows pending questions (admin only)"
)
@commands.has_permissions(administrator=True)
async def admins_show_pending_questions(ctx):
  discord_id = str(ctx.author.id)
  discord_name = str(ctx.author)
  await log_print(f'admins_show_pending_questions: {discord_name} {discord_id}')

  dm = ctx.channel
  q_ref = Questions_ref.where(u'status', u'!=', u'session-complete').stream() 

  cnt = 0
  for q in q_ref:
    cnt = cnt + 1
    question = q.to_dict()
    await dm.send(f'{cnt}: {question}')
    student_discord_id = question['student_id']
    tutor_discord_id = question['tutor_id']
    msg = ''
    if (student_discord_id):
      student_member = await get_member_from_id(bot, student_discord_id)
      msg = (f'student name {str(student_member)} -- ')

    if (tutor_discord_id):
      tutor_member = await get_member_from_id(bot, tutor_discord_id)
      msg += (f'tutor name {str(tutor_member)}')
  
    await dm.send(msg)



@bot.command(
  name="INSPIRE",
	help="Shows daily inspiration!",
	brief="Shows daily inspiration!"
)
async def show_daily_inspiration(ctx):
    quote = get_quote()
    await ctx.channel.send(quote)


@bot.event
async def on_ready():
  await delete_documents_in_collection(Logs_ref, 50)

  global all_tutor_subject_set
  msg = f'Bot has logged in as {bot.user}, Bot ID: {bot.user.id}'
    
  show_max_members = 20
  for guild in bot.guilds:
    member_count = len(guild.members)
    if (member_count < show_max_members):
      show_max_members = member_count
    msg += f' bot.guild={guild}, {guild.id}, member_count {member_count}, showing first {show_max_members}:'
    break

  await log_print(msg)

  all_members = bot.get_all_members()
  cnt = 0
  msg = ''
  for member in all_members:
    msg += f'{str(member)}, {member.id}\n'
    cnt += 1
    if (cnt > show_max_members):
      break
  await log_print(msg)

  #await DBG_initialization() 
  #await delete_documents_in_collection(Questions_ref, 50)
  #await show_collection(Questions_ref, 'Questions')

  all_tutor_subject_set = await get_all_tutor_subjects()
  await log_print(f'all tutor subjects: {all_tutor_subject_set}')



@bot.event
async def on_member_join(member):
  log_msg = f'on_member_join: {str(member)}, {member.id}'
  send_msg = f'Hi {str(member)}, welcome to join Ring-a-Bell Tutoring Server!'
  tutor_subjects = await get_one_tutor_subjects(member.id)
  if (tutor_subjects is not None):
    log_msg += f' Veteran subjects: {tutor_subjects}'
    send_msg += f' Veteran subjects: {tutor_subjects}'

  await log_print(log_msg)
  await member.channel.send(send_msg)

  await member.create_dm()
  await dm_matching_questions_for_tutor(member.dm_channel, str(member), str(member.id))



@bot.event
async def on_member_update(before, after):
  if (before.name.find('Bot') != -1):
    debug_print(f'skip Bot on_member_update')
    return

  debug_print(f'on_member_update before: {str(before)} {before.id}, {before.nick} {before.name} {before.display_name} {before.status}, {before.roles}')
  debug_print(f'on_member_update after: {str(after)} {after.id}, {after.nick} {after.name} {after.display_name} {after.status}, {after.roles}')

  await after.create_dm()

  #status: offline (invisible), online, dnd, idle
  if ((before.status != after.status) and str(after.status) == "online"):
    await after.dm_channel.send(f'{after.name}: welcome to be online on Ring-a-Bell Tutoring server.')
    if (await get_tutor(str(after.id)) is not None):
      await after.dm_channel.send('You may run GETQ command to check new questions!')
    #await dm_matching_questions_for_tutor(after.dm_channel, after.name, str(after.id))
  
  if (str(before) != str(after)):
    msg = (f'Got name change from {str(before)} to {str(after)}, status {before.status}:{after.status}')
    await after.dm_channel.send(msg)
    await update_discord_name(str(after.id), (str(after)))



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
  if (newchan is not None and newchan.category is not None and newchan.category.name == 'private_tutoring_rooms'):
      member_count = len(newchan.members)
      msg = (f'{datetime.now()}: {str(member)} is joining channel ')
      msg += (f'id={newchan.id} name={newchan.name} cat={newchan.category}, created_at: {newchan.created_at}, member_count_after_joining={len(newchan.members)}')
      await log_print(msg)

      v_channel_id = str(newchan.id)
      await update_voice_chan_start_questionDB(v_channel_id, member_count)


  # Disconnecting a tutoring call
  if (oldchan is not None and oldchan.category is not None and oldchan.category.name == 'private_tutoring_rooms'):
      # user (either student or tutor) is leaving private channel of private_tutoring_rooms.
      member_count = len(oldchan.members)
      msg = (f'{datetime.now()}: {str(member)} is leaving channel ')
      msg += (f'id={oldchan.id} name={oldchan.name} cat={oldchan.category}, created_at: {oldchan.created_at}, member_count_after_leaving={member_count}')
      await log_print(msg)

      # the first person leaving will mark session complete
      v_channel_id = str(oldchan.id)
      tutor_discord_id, student_discord_id, session_minutes = await update_question_session_complete(v_channel_id)
      if (session_minutes > 0):
        await update_tutor_total_session_minutes(tutor_discord_id, session_minutes)
        await update_student_total_session_minutes(student_discord_id, session_minutes)




@bot.listen()
async def on_message(message):
  if "tutorial" in message.content.lower():
    # in this case don't respond with the word "Tutorial" or you will call the on_message event recursively
      await message.channel.send('This is what you want http://youtube.com/fazttech')
      await bot.process_commands(message)

  if message.content.startswith('imageimagetest'):
    subject = message.content.split(" ")[1]
    print(f'subject={subject}')

    len_att = len(message.attachments)
    print(f'len attachment = {len_att}')
    if (len_att == 0):  # no image attachment, return
      return

    imgurl = message.attachments[0].url
    print(f'imgurl = ', imgurl)
    #await message.channel.send(f'got msg attachment={imgurl}')

    if (True):
      bell_member = await get_member_from_id(bot, bell_discord_id)
      print(f'{str(bell_member)} name={bell_member.name}, id={bell_member.id}')
      await bell_member.create_dm()
      await bell_member.dm_channel.send(message.content)
      #await bell_member.dm_channel.send(f'{subject} {extra_txt}')
      await bell_member.dm_channel.send(f'relay msg attachment={imgurl}')
  
    await bot.process_commands(message)


print('running bot')
bot.run(TOKEN)
