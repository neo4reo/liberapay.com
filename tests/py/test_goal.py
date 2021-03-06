from __future__ import print_function, unicode_literals

from liberapay.testing import EUR, Harness


class Tests(Harness):

    def setUp(self):
        self.alice = self.make_participant('alice')

    def change_goal(self, goal, goal_custom="", auth_as="alice"):
        return self.client.PxST(
            "/alice/goal",
            {'goal': goal, 'goal_custom': goal_custom},
            auth_as=self.alice if auth_as == 'alice' else auth_as
        )

    def test_changing_to_minus_1_asks_confirmation(self):
        r = self.client.PxST('/alice/goal', {'goal': '-1'}, auth_as=self.alice)
        assert "Warning: Doing this will remove all the tips you are currently receiving." in r.text

    def test_wonky_custom_amounts_are_standardized(self):
        self.change_goal("custom", ",100,100.00001")
        alice = self.alice.from_id(self.alice.id)
        assert alice.goal == 100100

    def test_anonymous_gets_403(self):
        response = self.change_goal("100.00", auth_as=None)
        assert response.code == 403, response.code

    def test_invalid_is_400(self):
        response = self.change_goal("cheese")
        assert response.code == 400, response.code

    def test_invalid_custom_amount_is_400(self):
        response = self.change_goal("custom", "cheese")
        assert response.code == 400, response.code

    def test_change_goal(self):
        self.change_goal("custom", "100")
        self.change_goal("0")
        self.change_goal("custom", "1,100.00")
        self.change_goal("null", "")
        self.change_goal("custom", "400")

        actual = self.db.one("SELECT goal FROM participants")
        assert actual == EUR('400.00')

        actual = self.db.all("""
            SELECT payload
              FROM events
             WHERE type = 'set_goal'
          ORDER BY ts DESC
        """)
        assert actual == ['400.00 EUR', None, '1100.00 EUR', '0.00 EUR', '100.00 EUR']

    def test_team_member_can_change_team_goal(self):
        team = self.make_participant('team', kind='group')
        team.add_member(self.alice)
        r = self.client.PxST(
            '/team/goal',
            {'goal': 'custom', 'goal_custom': '99.99'},
            auth_as=self.alice
        )
        assert r.code == 302
        assert team.refetch().goal == EUR('99.99')
