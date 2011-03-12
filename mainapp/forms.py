from django import forms
from django.template.loader import render_to_string
from django.core.mail import send_mail
from fixmystreet import settings
from mainapp.models import Ward, Report, ReportUpdate, ReportCategoryClass,ReportCategory,ReportSubscriber
from django.utils.translation import ugettext_lazy
from django.contrib.gis.geos import fromstr
from django.forms.util import ErrorDict

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100,
                           widget=forms.TextInput(attrs={ 'class': 'required' }),
                           label=ugettext_lazy('Name'))
    email = forms.EmailField(widget=forms.TextInput(attrs=dict({ 'class': 'required' },
                                                               maxlength=200)),
                             label=ugettext_lazy('Email'))
    body = forms.CharField(widget=forms.Textarea(attrs={ 'class': 'required' }),
                              label=ugettext_lazy('Message'))
    
    def save(self, fail_silently=False):
        message = render_to_string("emails/contact/message.txt", self.cleaned_data )
        send_mail('FixMyStreet.ca User Message from %s' % self.cleaned_data['email'], message, 
                   settings.EMAIL_FROM_USER,[settings.ADMIN_EMAIL], fail_silently=False)


class ReportUpdateForm(forms.ModelForm):
    class Meta:
        model = ReportUpdate
        fields = ( 'desc','author','email','phone')

class ReportSubscriberForm(forms.ModelForm):
    class Meta:
        model = ReportSubscriber
        fields = ( 'email', )
        
"""
    Do some pre-processing to
    render opt-groups (silently supported, but undocumented
    http://code.djangoproject.com/ticket/4412 )
"""
    
class CategoryChoiceField(forms.fields.ChoiceField):
    
    def __init__(self, required=True, widget=None, label=None,
                 initial=None, help_text=None, *args, **kwargs):
        # assemble the opt groups.
        choices = []
        choices.append( ('', ugettext_lazy("Select a Category")) )
        catclasses = ReportCategoryClass.objects.all()
        for catclass in catclasses:
            categories = catclass.reportcategory_set.all()
            values = []
            for category in categories:
                values.append((category.pk, category.name ))
            choices.append((catclass,values))
        super(CategoryChoiceField,self).__init__(choices,required,widget,label,initial,help_text)

    def clean(self, value):
        super(CategoryChoiceField,self).clean(value)
        try:
            model = ReportCategory.objects.get(pk=value)
        except ReportCategory.DoesNotExist:
            raise ValidationError(self.error_messages['invalid_choice'])
        return model


class ReportUpdateForm(forms.ModelForm):
    class Meta:
        model = ReportUpdate
        fields = ( 'desc','author','email','phone')


class ReportForm(forms.ModelForm):
    """
    ReportForm --
    combines is_valid(), clean(), and save()
    etc. for both an update form and a report form

    (information for both models is submitted at
    the same time when a report is initially created)
    """

    class Meta:
        model = Report
        fields = ('lat','lon','title', 'category', 'photo')

    category = CategoryChoiceField()
    lat = forms.fields.CharField(widget=forms.widgets.HiddenInput)
    lon = forms.fields.CharField(widget=forms.widgets.HiddenInput)

    def __init__(self,data=None,files=None,initial=None):
        self.update_form = ReportUpdateForm(data)
        super(ReportForm,self).__init__(data,files, initial=initial)
        
    def _get_pnt(self):
        lat = self.cleaned_data.get("lat")
        lon = self.cleaned_data.get("lon")
        pnt = fromstr("POINT(" + lon + " " + lat + ")", srid=4326)
        return(pnt)
    
    def _get_ward(self):
        pnt = self._get_pnt()
        try:
            ward = Ward.objects.get(geom__contains=pnt)
            return(ward)
        except:
            return( None )
    
    def clean(self):
        ward = self._get_ward()
        if not ward:
            raise forms.ValidationError("lat/lon not supported")

        # Always return the full collection of cleaned data.
        return self.cleaned_data

    def is_valid(self):
        update_valid = self.update_form.is_valid()
        report_valid = super(ReportForm,self).is_valid()
        return( update_valid and report_valid )
    
    def save(self, is_confirmed = False):
        report = super(ReportForm,self).save( commit = False )
        update = self.update_form.save(commit=False)
        
        #these are in the form for 'update'
        report.desc = update.desc
        report.author = update.author
        
        #this info is custom
        report.point = self._get_pnt()
        report.ward = self._get_ward()
        report.is_confirmed = is_confirmed
        update.report = report
        update.first_update = True
        update.is_confirmed = is_confirmed
        update.created_at = report.created_at
        report.save()
        update.report = report
        update.save()
        return( report )
    
    def all_errors(self):
        "returns errors for both report and update forms"
        errors = ErrorDict()
        for key,value in self.errors.items():
            errors[key] = value
        # add errors from the update form to the end.
        for key,value in self.update_form.errors.items():
            errors[key] = value
            
        return( errors )


