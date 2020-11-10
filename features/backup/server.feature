Feature: server

	@test @case.272
	Scenario: server/list should return server list
	  When I get servers list
	  Then the response is a non-empty list
	  And the response list columns are not empty: server_id, server_ip, time_stamp
	  And the response list has a record whose ucore_status is "STATUS_OK(leader)"

	@test @case.272
	Scenario Outline: server/install should install component
	  When I found a server without component <component>, or I skip the test
	  And I install a component <component> on the server
	  Then the response is ok
	  And the server should has component <component> 
	  And the server's component <component> should be installed as the standard
	  

	Examples: install all components
		| component |
		| ucore |
		#| uagent |
		| umc |
		| udeploy |
		| uguard-mgr |
		| uguard-agent |
		| umon |
		#| ulogstash |
		#| uelasticsearch |
		| urman-mgr |
		| urman-agent |
		| uterm |
		| usql |
		| urds |
		#| ustats |

	@test @case.272
	Scenario: server/prepare_server_env_for_guard should install components
	  When I found a server without components udeploy,uguard-agent,urman-agent, or I skip the test
	  And I prepare the server for uguard
	  Then the response is ok
	  And the server should has components udeploy,ustats,uguard-agent,urman-agent
	  And the server's components udeploy,ustats,uguard-agent,urman-agent should be installed as the standard

	@test @case.272
	Scenario: server/prepare_server_env_for_guard_manager should install components
	  When I found a server without components uguard-mgr,urman-mgr, or I skip the test
	  And I prepare the server for uguard manager
	  Then the response is ok
	  And the server should has components uguard-mgr,urman-mgr
	  And the server's components uguard-mgr,urman-mgr should be installed as the standard
