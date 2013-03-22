from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms.models import inlineformset_factory

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout, Div

from caminae.common.forms import CommonForm
from caminae.core.fields import TopologyField
from caminae.core.forms import TopologyForm
from caminae.core.widgets import TopologyReadonlyWidget
from caminae.infrastructure.models import BaseInfrastructure

from .models import Intervention, Project


class ManDayForm(forms.ModelForm):
    helper = FormHelper()

    def __init__(self, *args, **kwargs):
        super(ManDayForm, self).__init__(*args, **kwargs)
        self.helper.form_tag = False
        self.helper.layout = Layout('id',
                                    Div('nb_days', css_class="span1"),
                                    Div('job', css_class="span4"))
        self.fields['nb_days'].widget.attrs['class'] = 'span12'


ManDayFormSet = inlineformset_factory(Intervention, Intervention.jobs.through, form=ManDayForm, extra=1)


class FundingForm(forms.ModelForm):
    helper = FormHelper()

    def __init__(self, *args, **kwargs):
        super(FundingForm, self).__init__(*args, **kwargs)
        self.helper.form_tag = False
        self.helper.layout = Layout('id',
                                    Div('amount', css_class="span1"),
                                    Div('organism', css_class="span4"))
        self.fields['amount'].widget.attrs['class'] = 'span12'
        self.fields['organism'].widget.attrs['class'] = 'input-xlarge'


FundingFormSet = inlineformset_factory(Project, Project.founders.through, form=FundingForm, extra=1)


class InterventionForm(CommonForm):
    """ An intervention can be a Point or a Line """
    topology = TopologyField(label="")
    infrastructure = forms.ModelChoiceField(required=False,
                                            queryset=BaseInfrastructure.objects.existing(),
                                            widget=forms.HiddenInput())
    modelfields = ('name',
                   'date',
                   'status',
                   'disorders',
                   'type',
                   'comments',
                   'in_maintenance',
                   'height',
                   'width',
                   'material_cost',
                   'heliport_cost',
                   'subcontract_cost',
                   'stake',
                   'project',
                   'infrastructure')
    geomfields = ('topology',
                  Fieldset(_("Mandays"),))

    class Meta(CommonForm.Meta):
        model = Intervention
        exclude = ('deleted', 'geom', 'jobs')

    MEDIA_JS = TopologyForm.MEDIA_JS


    def __init__(self, *args, **kwargs):
        super(InterventionForm, self).__init__(*args, **kwargs)
        # If we create or edit an intervention on infrastructure, set
        # topology field as read-only
        infrastructure = kwargs.get('initial', {}).get('infrastructure')
        if self.instance.on_infrastructure:
            infrastructure = self.instance.topology
        if infrastructure:
            self.helper.form_action += '?infrastructure=%s' % infrastructure.pk
            self.fields['topology'].widget = TopologyReadonlyWidget()
            self.fields['topology'].label = _(infrastructure.kind.capitalize())

    def clean(self, *args, **kwargs):
        # If topology was read-only, topology field is empty, get it from infra.
        cleaned_data = super(InterventionForm, self).clean()
        if 'infrastructure' in self.cleaned_data and \
           'topology' not in self.cleaned_data:
            self.cleaned_data['topology'] = self.cleaned_data['infrastructure']
        return cleaned_data

    def save(self, *args, **kwargs):
        infrastructure = self.cleaned_data.get('infrastructure')
        if infrastructure:
            self.instance.set_infrastructure(infrastructure)
        return super(InterventionForm, self).save(*args, **kwargs)


class InterventionCreateForm(InterventionForm):
    def __init__(self, *args, **kwargs):
        # If we create an intervention on infrastructure, get its topology
        initial = kwargs.get('initial', {})
        infrastructure = initial.get('infrastructure')
        if infrastructure:
            initial['topology'] = infrastructure
        kwargs['initial'] = initial
        super(InterventionCreateForm, self).__init__(*args, **kwargs)

    class Meta(InterventionForm.Meta):
        exclude = InterventionForm.Meta.exclude + (
            'height',
            'width',
            'material_cost',
            'heliport_cost',
            'subcontract_cost',
            'stake',
            'project',)


class ProjectForm(CommonForm):
    modelfields = ('name',
                   'type',
                   'domain',
                   'begin_year',
                   'end_year',
                   'constraint',
                   'cost',
                   'comments')
    geomfields = ('contractors',
                  'project_owner',
                  'project_manager',
                  Fieldset(_("Fundings"),))  # no geom field in project

    class Meta:
        model = Project
        exclude = ('deleted', 'founders')

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        self.helper.form_tag = False
