set(CURR_DIR ${QL_DESIGNS_DIR}/counter_4clk)
add_file_target(FILE ${CURR_DIR}/counter_4clk.v SCANNER_TYPE verilog)
add_file_target(FILE counter_4clk.sdc SCANNER_TYPE)
add_file_target(FILE test.pcf)

add_fpga_target(
  NAME counter_4clk-umc22-no-adder
  TOP top
  BOARD qlf_k4n8-qlf_k4n8_umc22_slow_board
  SOURCES ${CURR_DIR}/counter_4clk.v
  INPUT_IO_FILE test.pcf
  INPUT_SDC_FILE counter_4clk.sdc
  EXPLICIT_ADD_FILE_TARGET
  NET_PATCH_EXTRA_ARGS "--pcf-constraints ${CMAKE_CURRENT_SOURCE_DIR}/test.pcf"
  DEFINES SYNTH_OPTS=-no_adder
)

add_fpga_target(
  NAME counter_4clk-umc22-adder
  TOP top
  BOARD qlf_k4n8-qlf_k4n8_umc22_slow_board
  SOURCES ${CURR_DIR}/counter_4clk.v
  INPUT_IO_FILE test.pcf
  INPUT_SDC_FILE counter_4clk.sdc
  EXPLICIT_ADD_FILE_TARGET
  NET_PATCH_EXTRA_ARGS "--pcf-constraints ${CMAKE_CURRENT_SOURCE_DIR}/test.pcf"
)

add_dependencies(all_qlf_k4n8_tests_no_adder counter_4clk-umc22-no-adder_bit)
add_dependencies(all_qlf_k4n8_tests_adder    counter_4clk-umc22-adder_bit)
