from judge.models import Clarification
from django import forms

class ClarificationForm(forms.ModelForm):
    asker = None
    problem = None

    class Meta:
        model = Clarification
        fields = [ 'question' ]
        widgets = {'question': forms.widgets.Textarea(attrs={'placeholder':"Type your question here"})}
        labels = {'question': "Enter your question:"}

    def __init__(self, asker=None, problem=None, **kwargs):
        self.asker = asker
        self.problem = problem
        return super().__init__(**kwargs)

    def save(self, commit=True):
        self.instance.owner = self.asker
        self.instance.problem = self.problem
        return super().save(commit=commit)
