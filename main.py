import json
import os.path

from kivymd.app import MDApp
from kivy.lang.builder import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from functools import partial
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
import traceback
from kivymd.uix.button import MDRoundFlatButton
import random

class MenuScreen(Screen):
    group_list_layout = ObjectProperty()

    def __init__(self, **kwargs):
        super(MenuScreen, self).__init__(**kwargs)
        self.group_list_layout = MDGridLayout(cols=1, size_hint_y=None)

        # Wrap the group list layout in a ScrollView
        self.scroll_view = ScrollView(size_hint=(1, None), size=(Window.width, Window.height - dp(56)))  
        self.scroll_view.add_widget(self.group_list_layout)
        self.add_widget(self.scroll_view)

    def on_pre_enter(self, *args):
        self.update_group_list()

    def on_right_action_items(self, instance):
        self.manager.current = 'stats'

    def update_group_list(self):
        try:
            self.group_list_layout.clear_widgets()
            with open("user_data.json", "r") as file:
                data = json.load(file)

            for group_data in data:
                group_name = group_data.get("name_group", "")
                if group_name:
                    card = MDCard(
                        orientation='vertical',
                        size_hint_y=None,
                        height=dp(80),
                        elevation=1,
                        on_release=partial(self.show_flashcards_screen, group_data)
                    )

                    box_layout = BoxLayout(padding=(dp(16), 0))
                    label = MDLabel(
                        text=group_name,
                        theme_text_color="Primary",
                        halign="left",
                        valign="center",
                    )

                    box_layout.add_widget(label)
                    card.add_widget(box_layout)
                    self.group_list_layout.add_widget(card)

        except FileNotFoundError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"An error occurred: {traceback.format_exc()}")

    def show_flashcards_screen(self, group_data, *args):
        self.manager.current = 'flashcards'
        flashcards_screen = self.manager.get_screen('flashcards')
        flashcards_screen.group_data = group_data
        flashcards_screen.load_flashcards()

class CreateScreen(Screen):
    card_list_layout = ObjectProperty()

    def on_left_action_items(self, instance):
        self.manager.current = 'menu'

    def __init__(self, **kwargs):
        super(CreateScreen, self).__init__(**kwargs)
        self.card_data = []

    def add_card(self):
        card_container = self.ids.card_container

        new_card = MDCard(
            orientation='vertical',
            size_hint_y=None,
            height="80dp",
            elevation=1,
        )

        new_box_layout = MDGridLayout(
            cols=2,
            row_default_height="40dp",
            row_force_default=True,
            spacing='10dp',
            padding='10dp',
        )

        new_question_field = MDTextField(hint_text='Question')
        new_answer_field = MDTextField(hint_text='Answer')

        new_box_layout.add_widget(new_question_field)
        new_box_layout.add_widget(new_answer_field)

        close_button = MDIconButton(
            icon="close",
            theme_text_color="Custom",
            text_color=(1, 0, 0, 1),
            pos_hint={"center_x": 0.95, "center_y": 0.9},
        )

        close_button.bind(
            on_release=lambda x: self.remove_card(new_card, new_question_field, new_answer_field))

        new_card.add_widget(new_box_layout)
        new_card.add_widget(close_button)

        card_container.add_widget(new_card, index=0)

        # Store the text fields for later retrieval
        self.card_data.append({'question_field': new_question_field, 'answer_field': new_answer_field})

    def remove_card(self, card, question_field, answer_field):
        # Remove the card from the UI and the card data list
        self.ids.card_container.remove_widget(card)
        self.card_data.remove({'question_field': question_field, 'answer_field': answer_field})

    def save_to_json(self):
        # Gather data and print to console
        group_name = self.ids.group_name.text

        data = []
        if os.path.exists("user_data.json"):
            with open('user_data.json') as file:
                data = json.load(file)

        new_data = {
            'name_group': group_name,
            'flashcards': []
        }

        for card in self.card_data:
            question = card['question_field'].text
            answer = card['answer_field'].text
            new_data['flashcards'].append({
                'question': question,
                'answer': answer
            })

            # Clear the text fields
            card['question_field'].text = ''
            card['answer_field'].text = ''

        data.append(new_data)
        with open('user_data.json', 'w') as file:
            json.dump(data, file, indent=4)

        # Show success dialog
        self.show_success_dialog()

        # Clear the group name field
        self.ids.group_name.text = ''

        # Clear the internal card data list
        self.card_data.clear()

        # Navigate back to the MenuScreen
        self.manager.current = 'menu'

    def show_success_dialog(self):
        success_dialog = MDDialog(
            title="Success",
            text="Flashcards saved successfully!",
            buttons=[MDFlatButton(text="OK", on_release=lambda x: success_dialog.dismiss())],
        )
        success_dialog.open()

class FlashcardsScreen(Screen):
    def __init__(self, group_data=None, **kwargs):
        super().__init__(**kwargs)
        self.group_data = group_data
        self.layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))

        self.flashcard_list = MDList()
        self.scroll_view = ScrollView(size_hint=(1, None), size=(Window.width, Window.height - dp(120)))
        self.scroll_view.add_widget(self.flashcard_list)

        self.layout.add_widget(self.scroll_view)
        self.add_widget(self.layout)
        self.current_card_index = 0

        self.save_button = MDRoundFlatButton(
            text='Save Changes',
            size_hint=(None, None),
            size=(dp(200), dp(48)),
            pos_hint={'center_x': 0.5},
            on_release=self.save_flashcards
        )

        self.layout.add_widget(self.save_button)

    def on_left_action_items(self, instance):
        self.manager.current = 'menu'

    def on_right_action_items(self, instance):
        self.manager.current = 'study'

    def on_pre_enter(self, *args):
        if self.group_data:
            self.load_flashcards()

    def load_flashcards(self):
        self.flashcard_list.clear_widgets()
        flashcards = self.group_data.get('flashcards', [])
        for flashcard in flashcards:
            self.add_flashcard(flashcard['question'], flashcard['answer'])

    def add_flashcard(self, question='', answer=''):
        new_card = MDCard(
            orientation='vertical',
            size_hint_y=None,
            height=dp(100),
            padding=dp(10),
            spacing=dp(10),
            elevation=1,
        )

        box_layout = MDGridLayout(
            cols=2,
            row_default_height=dp(40),
            row_force_default=True,
            spacing=dp(10),
            padding=dp(10),
        )

        question_field = MDTextField(
            hint_text='Question',
            text=question
        )

        answer_field = MDTextField(
            hint_text='Answer',
            text=answer
        )

        box_layout.add_widget(question_field)
        box_layout.add_widget(answer_field)

        new_card.question_field = question_field
        new_card.answer_field = answer_field

        new_card.add_widget(box_layout)
        self.flashcard_list.add_widget(new_card)

    def save_flashcards(self, *args):
        data = []
        if os.path.exists("user_data.json"):
            with open('user_data.json') as file:
                data = json.load(file)

        for group in data:
            if group['name_group'] == self.group_data['name_group']:
                group['flashcards'] = []  # Clear existing flashcards
                for flashcard_item in self.flashcard_list.children:
                    flashcard = {
                        'question': flashcard_item.question_field.text,
                        'answer': flashcard_item.answer_field.text,
                    }
                    group['flashcards'].append(flashcard)
                break

        with open('user_data.json', 'w') as file:
            json.dump(data, file, indent=4)

        # Show success dialog
        self.show_success_dialog()

    def show_success_dialog(self):
        success_dialog = MDDialog(
            title="Success",
            text="Flashcards saved successfully!",
            buttons=[MDFlatButton(text="OK", on_release=lambda x: success_dialog.dismiss())]
        )
        success_dialog.open()

    def delete_group(self):
        dialog = MDDialog(
            title="Delete Group",
            text="Are you sure you want to delete this group?",
            buttons=[
                MDFlatButton(
                    text="Cancel",
                    on_release=lambda *args: dialog.dismiss()
                ),
                MDFlatButton(
                    text="Delete",
                    on_release=self.confirm_delete_group
                )
            ]
        )
        dialog.open()

    def confirm_delete_group(self, *args):
        dialog = args[0].parent.parent.parent
        data = []
        if os.path.exists("user_data.json"):
            with open('user_data.json') as file:
                data = json.load(file)

        data = [group for group in data if group['name_group'] != self.group_data['name_group']]

        with open('user_data.json', 'w') as file:
            json.dump(data, file, indent=4)

        self.manager.current = 'menu'
        self.manager.get_screen('menu').update_group_list()
        self.manager.current = 'menu'

class StudyScreen(Screen):
    current_flashcard = None
    flashcards_data = []
    correct_answers = 0
    incorrect_answers = 0

    def on_left_action_items(self, instance):
        self.manager.current = 'menu'

    def on_pre_enter(self, *args):
        self.load_flashcards()

    def load_flashcards(self):
        self.current_flashcard = None

        flashcards = self.manager.get_screen('flashcards').group_data.get('flashcards', [])
        self.flashcards_data = [{"question": f["question"], "answer": f["answer"]} for f in flashcards]
        random.shuffle(self.flashcards_data)

        if self.flashcards_data:
            self.current_flashcard = self.flashcards_data.pop()
            self.ids.question_label.text = self.current_flashcard["question"]
            self.ids.answer_input.text = ''
        else:
            self.ids.question_label.text = "No more flashcards available."
            self.ids.answer_input.text = ''
            self.ids.check_button.disabled = True

    def check_answer(self):
        user_answer = self.ids.answer_input.text
        correct_answer = self.current_flashcard["answer"]

        if user_answer.lower() == correct_answer.lower():
            self.correct_answers += 1
        else:
            self.incorrect_answers += 1
            self.show_wrong_answer_dialog(correct_answer)

        self.load_flashcards()

    def show_wrong_answer_dialog(self, correct_answer):
        wrong_answer_dialog = MDDialog(
            title="Incorrect Answer",
            text=f"Sorry, your answer is incorrect. The correct answer is:\n{correct_answer}"
        )
        wrong_answer_dialog.open()

    def on_leave(self, *args):
        # Display the stats when leaving the study screen
        self.show_stats_dialog()

    def show_stats_dialog(self):
        stats_dialog = MDDialog(
            title="Study Stats",
            text=f"Correct Answers: {self.correct_answers}\nIncorrect Answers: {self.incorrect_answers}",
            buttons=[MDFlatButton(text="OK", on_release=lambda x: stats_dialog.dismiss())],
        )
        stats_dialog.open()

class Answa(MDApp):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(CreateScreen(name='create'))
        sm.add_widget(FlashcardsScreen(name='flashcards'))
        sm.add_widget(StudyScreen(name='study'))

        return Builder.load_file('main.kv')

if __name__ == '__main__':
    Answa().run()