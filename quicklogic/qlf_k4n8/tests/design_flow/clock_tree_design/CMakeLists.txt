set(CURR_DIR ${QL_DESIGNS_DIR}/clock_tree_design)
add_file_target(FILE ${CURR_DIR}/clock_tree_design.v SCANNER_TYPE verilog)

add_fpga_target(
  NAME clock_tree_design_test-umc22-no-adder
  TOP clock_tree_design
  BOARD qlf_k4n8-qlf_k4n8_umc22_slow_board
  SOURCES ${CURR_DIR}/clock_tree_design.v
  EXPLICIT_ADD_FILE_TARGET
  DEFINES SYNTH_OPTS=-no_adder
  )

add_fpga_target(
  NAME clock_tree_design_test-umc22-adder
  TOP clock_tree_design
  BOARD qlf_k4n8-qlf_k4n8_umc22_slow_board
  SOURCES ${CURR_DIR}/clock_tree_design.v
  EXPLICIT_ADD_FILE_TARGET
  )

add_dependencies(all_qlf_k4n8_tests_no_adder clock_tree_design_test-umc22-no-adder_bit)
add_dependencies(all_qlf_k4n8_tests_adder    clock_tree_design_test-umc22-adder_bit)
