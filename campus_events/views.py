from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from .models import CampusEvent
from django.utils import timezone
import json

class EventListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        events = CampusEvent.objects.filter(date__gte=timezone.now()).order_by('date')
        past_events = CampusEvent.objects.filter(date__lt=timezone.now()).order_by('-date')[:10]
        context = {
            'upcoming_events': events,
            'past_events': past_events,
            'can_manage': request.user.role in ['Teacher', 'Management', 'Admin'] or request.user.is_superuser
        }
        return render(request, 'campus_events/list.html', context)

class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role in ['Teacher', 'Management', 'Admin'] or self.request.user.is_superuser

    def post(self, request, *args, **kwargs):
        try:
            title = request.POST.get('title')
            description = request.POST.get('description')
            category = request.POST.get('category')
            date_str = request.POST.get('date')
            location = request.POST.get('location')
            organizer = request.POST.get('organizer')
            image = request.FILES.get('image')

            if not all([title, description, date_str, location, organizer]):
                return JsonResponse({'status': 'error', 'message': 'All fields are required'}, status=400)

            event = CampusEvent.objects.create(
                title=title,
                description=description,
                category=category,
                date=date_str,
                location=location,
                organizer=organizer,
                image=image,
                created_by=request.user
            )
            return JsonResponse({'status': 'success', 'message': 'Event created successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class EventsAJAX(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        events = CampusEvent.objects.filter(date__gte=timezone.now()).order_by('date')[:3]
        data = []
        for e in events:
            data.append({
                'id': e.id,
                'title': e.title,
                'description': e.description[:100],
                'date': e.date.strftime('%b %d'),
                'location': e.location,
                'organizer': e.organizer,
                'category': e.category
            })
        return JsonResponse({'status': 'success', 'events': data})

class EventDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role in ['Teacher', 'Management', 'Admin'] or self.request.user.is_superuser

    def post(self, request, pk, *args, **kwargs):
        event = get_object_or_404(CampusEvent, pk=pk)
        event.delete()
        return JsonResponse({'status': 'success'})
