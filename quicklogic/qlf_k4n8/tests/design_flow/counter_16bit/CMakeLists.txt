set(CURR_DIR ${QL_DESIGNS_DIR}/counter_16bit)
add_file_target(FILE ${CURR_DIR}/counter_16bit.v SCANNER_TYPE verilog)

add_fpga_target(
  NAME counter_16bit_test-umc22-no-adder
  TOP top
  BOARD qlf_k4n8-qlf_k4n8_umc22_slow_board
  SOURCES ${CURR_DIR}/counter_16bit.v
  EXPLICIT_ADD_FILE_TARGET
  DEFINES SYNTH_OPTS=-no_adder
)

add_fpga_target(
  NAME counter_16bit_test-umc22-adder
  TOP top
  BOARD qlf_k4n8-qlf_k4n8_umc22_slow_board
  SOURCES ${CURR_DIR}/counter_16bit.v
  EXPLICIT_ADD_FILE_TARGET
)

add_dependencies(all_qlf_k4n8_tests_no_adder counter_16bit_test-umc22-no-adder_bit)
add_dependencies(all_qlf_k4n8_tests_adder    counter_16bit_test-umc22-adder_bit)
