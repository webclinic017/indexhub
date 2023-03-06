import React from "react";
import {
  Box,
  Divider,
  FormControl,
  FormLabel,
  Stack,
  Text,
} from "@chakra-ui/react";
import { Select, MultiValue } from "chakra-react-select";
import { SelectedSource, Source } from "../sources/sources_table";

const setColumnValue = (
  values: MultiValue<Record<any, string>>, // eslint-disable-line @typescript-eslint/no-explicit-any
  set_func: React.Dispatch<React.SetStateAction<any>> // eslint-disable-line @typescript-eslint/no-explicit-any
) => {
  const columns: string[] = [];
  values.map((value) => {
    columns.push(value.value);
  });
  set_func(columns);
};

const getOptions = (options: string[]) => {
  const result: Record<any, string>[] = []; // eslint-disable-line @typescript-eslint/no-explicit-any
  options.forEach((option) => {
    result.push({
      value: option,
      label: option,
    });
  });
  return result;
};

const getOptionsSource = (sources: Source[]) => {
  const result: Record<any, any>[] = []; // eslint-disable-line @typescript-eslint/no-explicit-any
  sources.forEach((source) => {
    if (source.status == "COMPLETE") {
      result.push({
        value: {
          id: source.id,
          name: source.name,
          entity_cols: source.entity_cols,
          target_cols: source.target_cols,
        },
        label: source.name,
      });
    }
  });
  return result;
};

const NewReport = (props: {
  source_name: string;
  entity_cols: string[];
  target_cols: string[];
  sources: Source[];
  new_report: boolean;
  setSelectedSource: React.Dispatch<React.SetStateAction<SelectedSource>>;
  setSelectedLevelCols: React.Dispatch<React.SetStateAction<never[]>>;
  setSelectedTargetCol: React.Dispatch<React.SetStateAction<string>>;
}) => {
  return (
    <Box
      as="form"
      borderColor="forms.border"
      borderWidth="1px"
      borderStyle="solid"
      borderRadius="lg"
    >
      <Stack
        spacing="5"
        px={{ base: "4", md: "6" }}
        py={{ base: "5", md: "6" }}
      >
        {props.new_report ? (
          <FormControl isRequired>
            <FormLabel>Source: </FormLabel>
            <Select
              onChange={(value) =>
                props.setSelectedSource(value ? value.value : {})
              }
              options={getOptionsSource(props.sources)}
            />
          </FormControl>
        ) : (
          <Text>
            Source name: <b>{props.source_name}</b>
          </Text>
        )}
        <FormControl isRequired>
          <FormLabel>Target column</FormLabel>
          <Select
            onChange={(value) =>
              props.setSelectedTargetCol(value ? value.value : "")
            }
            options={getOptions(props.target_cols)}
          />
        </FormControl>
        <FormControl isRequired>
          <FormLabel>Level(s)</FormLabel>
          <Select
            onChange={(value) =>
              setColumnValue(value, props.setSelectedLevelCols)
            }
            options={getOptions(props.entity_cols)}
            isMulti
          />
        </FormControl>
      </Stack>
      <Divider />
    </Box>
  );
};

export default NewReport;
