import json

templates = None

with open("src/templates.json", 'r', encoding="utf-8") as f:
    templates = json.load(f)

def day_stats_gen():
    message = """
        # Увага члени **СУКАЧАТ**у
        Cьогоднішній вбивця нашого улюбленого чату є
        Пан **{0}**(aka {1}) з ЛЕГЕНДАРНИМИ {2} в онлайні та {3} у войсі
        Щиро дякую вам за ваш вклад у знеживлені нашого чату, сподіваюсь ця цифра ставатиме тільки меншою :)
        """
#        ## Honorable mention
#        {4}(aka {5}) {6}(aka {7}) зробили сьогодні також великий внесок і заслуговують на похвалу. Так тримати!
#        """
    return [message, templates]