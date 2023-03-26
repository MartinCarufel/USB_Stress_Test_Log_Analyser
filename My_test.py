import re
import unittest
import main


class Test_main(unittest.TestCase):

    def test_data_extractor(self):
        csv_data = main.extract_stress_test_data("usb_stress_testIO-04-000979.log")
        # csv_data = []
        self.assertTrue(len(csv_data) != 0)

    def test_extractor_return_all_column_data(self):
        csv_data = main.extract_stress_test_data("usb_stress_testIO-04-000979.log")
        for row_id in range(len(csv_data)):
            self.assertTrue(len(csv_data[row_id]) == 12)

    def test_convert_listcsv_to_dataframe_size(self):
        test_data = [['1.00', '30', '0', '0', '30', '0', '30.00', '295.42', '0', '0', '0', '0'],
                     ['2.00', '60', '0', '0', '30', '0', '30.00', '295.37', '0', '0', '0', '0'],
                     ['3.00', '90', '0', '0', '30', '0', '30.00', '295.49', '0', '0', '0', '0'],
                     ['4.00', '120', '0', '0', '30', '0', '30.00', '295.51', '0', '0', '0', '0'],
                     ['5.00', '150', '0', '0', '30', '0', '30.00', '295.45', '0', '0', '0', '0']]

        df = main.convert_listcsv_to_dataframe(test_data)
        self.assertTupleEqual((5,12),df.shape)

    def test_convert_listcsv_to_dataframe_header(self):
        test_data = [['1.00', '30', '0', '0', '30', '0', '30.00', '295.42', '0', '0', '0', '0']]

        df = main.convert_listcsv_to_dataframe(test_data)
        df_created_header = []
        expected_df_header = ["Duration", "# Total Frame", "# total bad pkt", "# total dropped", "# frames",
              "# dropped", "avg. fps", "MB/s", "#C0 Dead img", "#C1 Dead img", "#C2 Dead img", "#C3 Dead img"]
        for i in df.columns:
            df_created_header.append(i)
        self.assertListEqual(df_created_header, expected_df_header)
        # print(df.columns)

    def test_get_path_list_from_file_not_empty(self):
        self.assertTrue(True)
        pass

    def test_get_path_list_from_file_BS_to_FS(self):
        """
        Test the function get_path_list_from_file conversion the backslash into forwardslash
        """
        function_result = main.get_path_list_from_file("Test_file.txt")

        for file in function_result:
            self.assertNotRegex(text=file, unexpected_regex="\\\\")
            self.assertNotRegex(text=file, unexpected_regex="\\n")

        # print(function_result)

class Test_secondary(unittest.TestCase):
    def test_get_path_list_from_file_not_empty(self):
        file_list = main.get_path_list_from_file("new 1.txt")
        self.assertTrue(len(file_list) > 0)
        # print(file_list)
        pass

if __name__ == '__main__':
    unittest.main()