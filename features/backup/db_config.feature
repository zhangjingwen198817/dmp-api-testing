Feature: db_config

	@test @case.272
	Scenario Outline: update MySQL configuration should succeed
	  When I found a running MySQL instance, or I skip the test
	  And I update MySQL configuration "<option>" to "<option_value>"
	  Then the response is ok
	  When I wait for updating MySQL configuration finish in 1m
	  And I query the MySQL instance "show global variables like '<option>'"
	  Then the MySQL response should be
    	| Variable_name      | Value  |
    	| <option>  | <option_value>    |

	Examples: 
		| option | option_value |
		| slave_net_timeout | 999 |
		| slave_net_timeout | 998 |
		| slave_net_timeout | 997 |