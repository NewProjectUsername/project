from django.views.decorators.csrf import csrf_exempt
import json
from Event.models import Event, Lecture
from Visitor.models import EventProfile
from .models import UhfTime
from django.http import JsonResponse
import uuid
from datetime import timedelta, timezone, datetime
from json import JSONEncoder
from django.db import models
import pytz
from django.db.models import Q

@csrf_exempt
def connectMethod(request):
		if request.method == 'POST':
			con = json.loads(request.body.decode('utf-8'))
			username = con['params']['username']
			password = con['params']['password']
			if Event.objects.filter(api_username=username, api_key=password):
				user = Event.objects.filter(api_username=username, api_key=password)
			else:
				return JsonResponse({"result":{"msg":"not ql","status": 2},"id":"connect","error": "no user"})
			if len(user[0].token) != 0:
				token = user[0].token
				return JsonResponse({"result":{"msg":"success","status": 1},"token":token,"error": "null"})
			else:
				token = uuid.uuid4().hex
				user.update(token=token)
				return JsonResponse({"result":{"msg":"success","status": 1},"token":token,"error": "null"})
		else:
			return JsonResponse({"result":{"msg":"no post","status": 2},"id":"connect","error": "no post"})

@csrf_exempt
def getVisitors(request):
	utc=pytz.UTC
	visitors_out = []
	if request.method == 'POST':
		con = json.loads(request.body.decode('utf-8'))
		token = con['params']['token']
		deviceId = con['params']['device_id']
		event = Event.objects.get(token=token)
		times = datetime.now()
		if Lecture.objects.filter(uhf_tracking=True, device_id=deviceId):
			if event:
				lecture = Lecture.objects.filter(Q(start_time__lte = utc.localize(times)) & Q(end_time__gte = utc.localize(times)), uhf_tracking=True, device_id=deviceId, event=event)
				if lecture:
					lecture = lecture[0]
					if utc.localize(times) >= lecture.start_time and utc.localize(times) <= lecture.end_time: 
						for visitor in EventProfile.objects.filter(event=event, lectures=lecture):		
							visitors_out.append({"name": visitor.name+" "+visitor.surname,
												 "participant_id": str.upper(visitor.uhf_id)})
						if lecture.access_control == True:
							return JsonResponse({"title": lecture.name,
											 	 "lesson_id": lecture.id,
											 	 "direction": 0 if lecture.device_entrance_position == 'R' else 1,
											 	 "input_verify": 1,
											 	 "visitors": visitors_out})
						else:
							return JsonResponse({"title": lecture.name,
												 "lesson_id": lecture.id,
								    			 "direction": 0 if lecture.device_entrance_position == 'R' else 1,
												 "input_verify": 0,
												 "visitors": visitors_out})
				else:
					return JsonResponse({"result":{"msg":"no lecture","status": 2},"id":"connect","error": "no lecture"})

	else:
		return JsonResponse({"result":{"msg":"no post","status": 2},"id":"connect","error": "no post"})

#toDO
@csrf_exempt
def setVisitors(request):
	if request.method == 'POST':
		visitors = json.loads(request.body.decode('utf-8'))
		event = Event.objects.filter(token=visitors['params']['token'])
		if event:
			for visitor in visitors['params']['participants']:
				if len(EventProfile.objects.filter(participant_id=visitor['participant_id'])) > 0:
					mod = UhfTime(lectures=Lecture.objects.get(id=visitor['lecture_id']),
								  event=event,
								  visitor=EventProfile.objects.get(uhf_id=visitor['uhf_id']),
								  direction=visitor['direction'],
								  device_id=visitor['DeviceId'],
								  time_of_sec=datetime.strptime(visitor['ReadDateTime'], '%d.%m.%Y %H:%M:%S'))
					mod.save()
				else:
					return JsonResponse({"result":{"msg":"success","status": 1},"id":"set-participants","error": "null"})
			for v in Visitor.objects.all():
				if (timezone.now()- v.created) < timedelta(seconds=60):
					return JsonResponse({"result":{"msg":"success","status": 2},"id":"set-participants","error": "null"})
			return JsonResponse({"result":{"msg":"success","status": 1},"id":"set-participants","error": "null"})
		return JsonResponse({"result":{"msg":"success","status": 3},"id":"set-participants","error": "Token not valid"})


@csrf_exempt
def getLectures(request):
	if request.method == 'POST':
		lec = []
		con = json.loads(request.body.decode('utf-8'))
		token = con['params']['token']
		lectures = Lecture.objects.filter(event__token=token, bar_tracking=True)
		for lecture in lectures:
			if lecture.track:
				lec.append({"lecture_name": lecture.name,
							"lecture_id": lecture.id,
							"section_name": lecture.track.name,
							"section_id": lecture.track.id,
							"lecture_room": lecture.lecture_room,
							"start_time_of_lecture": lecture.start_time,
							"end_time_of_lecture": lecture.end_time,
							"bar_tracking": lecture.bar_tracking
						 })
			else:
				lec.append({"lecture_name": lecture.name,
							"lecture_id": lecture.id,
							"section_name": None,
							"section_id": None,
							"lecture_room": lecture.lecture_room,
							"start_time_of_lecture": lecture.start_time,
							"end_time_of_lecture": lecture.end_time,
							"bar_tracking": lecture.bar_tracking
						 })
		return JsonResponse({"Lectures":lec,"token": token, "error": "null"})
	else:
	   return JsonResponse({"result":{"msg":"no post","status": 2},"id":"connect","error": "no post"})

@csrf_exempt
def getCheckingData(request):
	if request.method == 'POST':
		out = []
		lec = []
		lecReg = []
		con = json.loads(request.body.decode('utf-8'))
		token = con['params']['token']
		participants = EventProfile.objects.filter(event__token=token, is_finished=True)
		for participant in participants:
			times = UhfTime.objects.filter(user=participant, direction=0)
			for time in times:
			  lec.append({'name':time.lecture.name,
			  			  'start_time':time.lecture.start_time,
			  			  'end_time':time.lecture.end_time
			  	})

			for lecture in participant.lectures.all():
				lecReg.append({'lecture_name': lecture.name,
							   'lecture_id': lecture.id,
							   'start_time': lecture.start_time,
							   'end_time': lecture.end_time,
							   'lecture_room': lecture.lecture_room,
							   'bar_tracking': lecture.bar_tracking,
							   'device_id': lecture.device_id})

			out.append({'name': participant.name,
					   'suername': participant.surname,
					   'company': participant.company_name,
					   'lectures': lecReg,
					   'times': lec,
					   'barcode_no': participant.barcode_no,
					   'uhf_id': participant.uhf_id,
					   'nfc_id': participant.nfc_id
					   })
			lec = []
			lecReg = []
		return JsonResponse({"result":{"msg":"success","status": 1, "visitors":out},"token":token,"error": "null"})
	else:
	   return JsonResponse({"result":{"msg":"no post","status": 2},"id":"checkingData","error": "no post"})


@csrf_exempt
def setData(request):
	if request.method == 'POST':
		con = json.loads(request.body.decode('utf-8'))
		token = con['params']['token']
		event = Event.objects.get(token=token)
		if event:
			for visitor in con['params']['participants']:
				if len(EventProfile.objects.filter(barcode_no=visitor['barcode_no'])) > 0:
					mod = UhfTime(user=EventProfile.objects.get(barcode_no=visitor['barcode_no']),
								  event=event,
								  lecture=Lecture.objects.get(id=visitor['lecture_id']),
								  direction=visitor['direction'],
								  device_id="android",
								  time_of_sec=datetime.strptime(visitor['ReadDateTime'], '%d.%m.%Y %H:%M:%S'))
					mod.save()
				else:
					return JsonResponse({"result":{"msg":"error","status": 0, "visitors": None},"id":"setBarcode","error": "No user with this id"})
			return JsonResponse({"result":{"msg":"success","status": 1, "visitors": None},"token": token,"error": "null"})
	else:
	   return JsonResponse({"result":{"msg":"no post","status": 2},"id":"connect","error": "no post"})


@csrf_exempt
def setUHFData(request):
	if request.method == 'POST':
		con = json.loads(request.body.decode('utf-8'))
		token = con['params']['token']
		event = Event.objects.get(token=token)
		if event:
			for visitor in con['params']['participants']:
				if len(EventProfile.objects.filter(uhf_id=str.upper(visitor['uhf_id']))) > 0:
					mod = UhfTime(lecture=Lecture.objects.get(id=visitor['lecture_id']),
								  event=event,
								  user=EventProfile.objects.get(uhf_id=str.upper(visitor['uhf_id'])),
								  direction=visitor['direction'],
								  device_id=visitor['device_id'],
								  time_of_sec=datetime.strptime(visitor['ReadDateTime'], '%d.%m.%Y %H:%M:%S'))
					mod.save()
				else:
					return JsonResponse({"result":{"msg":"error","status": 0},"id":"setUHF","error": "No user with this id"})
			return JsonResponse({"result":{"msg":"success","status": 1},"id":"setUHF","error": "null"})
	else:
	   return JsonResponse({"result":{"msg":"no post","status": 2},"id":"connect","error": "no post"})


@csrf_exempt
def getVisitorsBar(request):
	if request.method == 'POST':
		con = json.loads(request.body.decode('utf-8'))
		token = con['params']['token']
		if Event.objects.get(token=token):
			lectures = LectureVisitors.objects.filter(event__token=token, bar_tracking=True)

			'''
			visitors_out = []
			for visitor in visitors:
				visitors_out.append({"name": visitor.name+" "+visitor.surname,
									 "participant_id": visitor.participant_id})

			return JsonResponse({"title": "",
								 "lesson_id": "N10",
								 "direction": 0,
								 "input_verify": 1,
								 "visitors":visitors_out})'''
	else:
		return JsonResponse({"result":{"msg":"no post","status": 2},"id":"connect","error": "no post"})


@csrf_exempt
def getVisitorsBarUHFTime(request):
	if request.method == 'POST':
		out = []
		con = json.loads(request.body.decode('utf-8'))
		token = con['params']['token']
		participant = con['params']['participant_id']
		uhfTime = UhfTime.objects.filter(user__participant_id = participant)
		for time in uhfTime:
		  out.append({"hall_name":time.lecture.name})
		return JsonResponse({"result":{"lectures":out},"token":token,"error": "null"})
	else:
	   return JsonResponse({"result":{"msg":"no post","status": 2},"id":"connect","error": "no post"})


@csrf_exempt
def getEventData(request):
	if request.method == 'POST':
		out = []
		con = json.loads(request.body.decode('utf-8'))
		token = con['params']['token']
		event = Event.objects.get(token=token)
		return JsonResponse({"result":{"name": event.name, 
									   "start_time": event.start_time,
									   "end_time": event.end_time,
									   "location": event.location,
									   "category": event.category.title,
									   "logo": str("https://staging.idconference.eu" + event.logo.url),
									   "card_designer": event.card_designer
									   },"token":token,"error": "null"})
	else:
	   return JsonResponse({"result":{"msg":"no post","status": 2},"id":"connect","error": "no post"})


def passageCalculation():
	for event in Event.objects.filter(calculated=False):
		#if datetime.now > event.end_time:
		print (event)
		createModel(event)
		event.calculated = True
		event.save()
		model = str(event.subdomain)(direction=1)
		model.save()
	return True


@csrf_exempt
def setVisitorsUHFModul(request):
	if request.method == 'POST':
		times = datetime.now()
		utc = pytz.UTC
		visitors = json.loads(request.body.decode('utf-8'))
		event = Event.objects.get(token=visitors['params']['token'])
		if event:
			for visitor in visitors['params']['participants']:
				if len(EventProfile.objects.filter(event=event, uhf_id=str.upper(visitor['participant_id']))) > 0:
					lecture = Lecture.objects.filter(Q(start_time__lte = utc.localize(times)) & Q(end_time__gte = utc.localize(times)), uhf_tracking=True, device_id=visitors['params']['device_id'], event=event)
					mod = UhfTime(lecture=lecture[0],
								  event=event,
								  user=EventProfile.objects.get(uhf_id=str.upper(visitor['participant_id'])),
								  direction=visitor['direction'],
								  device_id=visitors['params']['device_id'],
								  time_of_sec=datetime.strptime(visitor['ReadDateTime'], '%d.%m.%Y %H:%M:%S'))
					mod.save()

			return JsonResponse({"result":{"msg":"success","status": 1},"id":"set-participants","error": "null"})
		

def eventNewUsers(event):
	tab = []
	lec = []
	lecReg = []
	for participant in EventProfile.objects.filter(event=event):
		print (event)
		if (participant.updated_at > event.start_time) or (participant.created_at > event.start_time):
			times = UhfTime.objects.filter(user=participant, direction=0)
			for time in times:
			  lec.append({'name':time.lecture.name,
			  			  'start_time':time.lecture.start_time,
			  			  'end_time':time.lecture.end_time
			  	})

			for lecture in participant.lectures.all():
				lecReg.append({'lecture_name': lecture.name,
							   'lecture_id': lecture.id,
							   'start_time': lecture.start_time,
							   'end_time': lecture.end_time,
							   'lecture_room': lecture.lecture_room,
							   'bar_tracking': lecture.bar_tracking,
							   'device_id': lecture.device_id})


			tab.append({'name': participant.name,
					   'suername': participant.surname,
					   'company': participant.company_name,
					   'lectures': lecReg,
					   'times': lec,
					   'barcode_no': participant.barcode_no,
					   'uhf_id': participant.uhf_id,
					   'nfc_id': participant.nfc_id
					   })
	return tab


@csrf_exempt
def eventNewUsersPost(request):
	if request.method == 'POST':
		visitors = json.loads(request.body.decode('utf-8'))
		event = Event.objects.get(token=visitors['params']['token'])
		tab = []
		lec = []
		lecReg = []
		for participant in EventProfile.objects.filter(event=event):
			if (participant.updated_at > event.start_time) or (participant.created_at > event.start_time):
				times = UhfTime.objects.filter(user=participant, direction=0)
				for time in times:
				  lec.append({'name':time.lecture.name,
				  			  'start_time':time.lecture.start_time,
				  			  'end_time':time.lecture.end_time
				  	})

				for lecture in participant.lectures.all():
					lecReg.append({'lecture_name': lecture.name,
								   'lecture_id': lecture.id,
								   'start_time': lecture.start_time,
								   'end_time': lecture.end_time,
								   'lecture_room': lecture.lecture_room,
								   'bar_tracking': lecture.bar_tracking,
								   'device_id': lecture.device_id})


				tab.append({'name': participant.name,
						   'suername': participant.surname,
						   'company': participant.company_name,
						   'lectures': lecReg,
						   'times': lec,
						   'barcode_no': participant.barcode_no,
						   'uhf_id': participant.uhf_id,
						   'nfc_id': participant.nfc_id
						   })
				lec = []
				lecReg = []
		return JsonResponse({"result":{"msg":"success","status": 1, "visitors":tab},"token":visitors['params']['token'],"error": "null"})
	else:
	   return JsonResponse({"result":{"msg":"no post","status": 2},"id":"eventNewUsersPost","error": "no post"})


@csrf_exempt
def getCheckingDataParticipant(request):
	if request.method == 'POST':
		out = []
		lec = []
		lecReg = []
		con = json.loads(request.body.decode('utf-8'))
		token = con['params']['token']
		token = con['params']['barcode_no']
		participant = EventProfile.objects.get(event__token=token, is_finished=True, barcode_no=barcode_no)
		times = UhfTime.objects.filter(user=participant, direction=0)
		for time in times:
		  lec.append({'name':time.lecture.name,
		  			  'start_time':time.lecture.start_time,
		  			  'end_time':time.lecture.end_time
		  	})

		for lecture in participant.lectures.all():
			lecReg.append({'lecture_name': lecture.name,
						   'lecture_id': lecture.id,
						   'start_time': lecture.start_time,
						   'end_time': lecture.end_time,
						   'lecture_room': lecture.lecture_room,
						   'bar_tracking': lecture.bar_tracking,
						   'device_id': lecture.device_id})

		out.append({'name': participant.name,
				   'suername': participant.surname,
				   'company': participant.company_name,
				   'lectures': lecReg,
				   'times': lec,
				   'barcode_no': participant.barcode_no,
				   'uhf_id': participant.uhf_id,
				   'nfc_id': participant.nfc_id
				   })
		lec = []
		lecReg = []
		return JsonResponse({"result":{"msg":"success","status": 1, "visitors":out},"token":token,"error": "null"})
	else:
	   return JsonResponse({"result":{"msg":"no post","status": 2},"id":"checkingData","error": "no post"})