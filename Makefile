current_path = $(shell pwd)
default: prepare test
prepare:
	behave features/scenario_test_cases/prepare.feature
test:
	behave features/scenario_test_cases/1m1s_a1.feature  features/scenario_test_cases/1m1s_a2.feature features/scenario_test_cases/1m1s_a3.feature \
	features/scenario_test_cases/1m2s_b1.feature features/scenario_test_cases/1m2s_b2.feature features/scenario_test_cases/1m2s_b3.feature \
	features/scenario_test_cases/1m2s_b4.feature features/scenario_test_cases/1m2s_b5.feature features/scenario_test_cases/1m2s_b6.feature \
	features/scenario_test_cases/1m2s_b7.feature features/scenario_test_cases/1m2s_b8.feature features/scenario_test_cases/1m2s_b9.feature \
	features/scenario_test_cases/1m2s_b10.feature features/scenario_test_cases/1m2s_b11.feature features/scenario_test_cases/1m2s_b12.feature \
	features/scenario_test_cases/1m4s_c1.feature features/scenario_test_cases/1m4s_c2.feature features/scenario_test_cases/1m4s_c3.feature \
	features/scenario_test_cases/before_scenario_cases.feature  features/scenario_test_cases/after_scenario_cases.feature features/scenario_test_cases/uproxy.feature \
	features/scenario_test_cases/db_config.feature  features/scenario_test_cases/damage_scenario_cases.feature

install_deps:
	pip install -r requirements.txt
env_dmp:
	cd ${current_path}/deploy && make install
format: 
	yapf --recursive --in-place --style='{based_on_style: google, indent_width: 4}' .
config:
	behave features/debug.feature --no-capture --tags=config.group
