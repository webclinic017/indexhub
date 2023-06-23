import React from "react";
import {
  Box,
  Button,
  Divider,
  Flex,
  Stack,
  Text,
  StackDivider,
  Container,
} from "@chakra-ui/react";

const ConfirmCreateSource = (props: {
  source_configs: Record<string, any>;
  source_tag: string
  createSource: () => void;
  goToPrevStep: () => void;
  isCreatingSource: boolean
}) => {
  return (
    <Box
      as="form"
      borderColor="forms.border"
      borderWidth="1px"
      borderStyle="solid"
      borderRadius="lg"
    >
      <Box bgColor={"forms.bg_gray"} borderTopRadius="lg">
        <Text py="1rem" pl="1rem" color="muted" fontSize="sm">
          An overview of your new source setup
        </Text>
      </Box>
      <Divider />
      <Container maxWidth="unset" py="1rem">
        <Stack spacing="5">
          <Stack spacing="5" divider={<StackDivider />}>
            <Stack
              direction={{ base: "column", md: "row" }}
              spacing={{ base: "1.5", md: "8" }}
              justifyContent="space-between"
            >
              <Text width="30%" fontWeight="bold">
                Source name:
              </Text>
              <Text width="70%">{props.source_configs["source_name"]}</Text>
            </Stack>
            <Stack
              direction={{ base: "column", md: "row" }}
              spacing={{ base: "1.5", md: "8" }}
              justifyContent="space-between"
            >
              <Text width="30%" fontWeight="bold">
                Source path:
              </Text>
              <Text width="70%">
                {props.source_tag}://{props.source_configs["bucket_name"]}/{props.source_configs["object_path"]}
              </Text>
            </Stack>
            <Stack
              direction={{ base: "column", md: "row" }}
              spacing={{ base: "1.5", md: "8" }}
              justifyContent="space-between"
            >
              <Text width="30%" fontWeight="bold">
                Frequency:
              </Text>
              <Text width="70%">{props.source_configs["freq"]}</Text>
            </Stack>
            <Stack
              direction={{ base: "column", md: "row" }}
              spacing={{ base: "1.5", md: "8" }}
              justifyContent="space-between"
            >
              <Text width="30%" fontWeight="bold">
                Time col:
              </Text>
              <Text width="70%">{props.source_configs["time_col"]}</Text>
            </Stack>
            {(props.source_configs["target_col"] && props.source_configs["target_col"].length > 0) && (
              <Stack
                direction={{ base: "column", md: "row" }}
                spacing={{ base: "1.5", md: "8" }}
                justifyContent="space-between"
              >
                <Text width="30%" fontWeight="bold">
                  Target column
                </Text>
                <Text width="70%">{props.source_configs["target_col"]}</Text>
              </Stack>
            )}
            {(props.source_configs["entity_cols"] && props.source_configs["entity_cols"].length > 0) && (
              <Stack
                direction={{ base: "column", md: "row" }}
                spacing={{ base: "1.5", md: "8" }}
                justifyContent="space-between"
              >
                <Text width="30%" fontWeight="bold">
                  Entity column(s)
                </Text>
                <Text width="70%">{props.source_configs["entity_cols"].join(", ")}</Text>
              </Stack>
            )}
            {props.source_configs["quantity_col"] && (
              <Stack
                direction={{ base: "column", md: "row" }}
                spacing={{ base: "1.5", md: "8" }}
                justifyContent="space-between"
              >
                <Text width="30%" fontWeight="bold">
                  Quantity column:
                </Text>
                <Text width="70%">{props.source_configs["quantity_col"]}</Text>
              </Stack>
            )}
            {props.source_configs["invoice_col"] && (
              <Stack
                direction={{ base: "column", md: "row" }}
                spacing={{ base: "1.5", md: "8" }}
                justifyContent="space-between"
              >
                <Text width="30%" fontWeight="bold">
                  Invoice ID column:
                </Text>
                <Text width="70%">{props.source_configs["invoice_col"]}</Text>
              </Stack>
            )}
            {props.source_configs["product_col"] && (
              <Stack
                direction={{ base: "column", md: "row" }}
                spacing={{ base: "1.5", md: "8" }}
                justifyContent="space-between"
              >
                <Text width="30%" fontWeight="bold">
                  Product ID column:
                </Text>
                <Text width="70%">{props.source_configs["product_col"]}</Text>
              </Stack>
            )}
            {props.source_configs["price_col"] && (
              <Stack
                direction={{ base: "column", md: "row" }}
                spacing={{ base: "1.5", md: "8" }}
                justifyContent="space-between"
              >
                <Text width="30%" fontWeight="bold">
                  Price column:
                </Text>
                <Text width="70%">{props.source_configs["price_col"]}</Text>
              </Stack>
            )}
            {props.source_configs["feature_cols"] && (
              <Stack
                direction={{ base: "column", md: "row" }}
                spacing={{ base: "1.5", md: "8" }}
                justifyContent="space-between"
              >
                <Text width="30%" fontWeight="bold">
                  Feature column(s):
                </Text>
                <Text width="70%">{props.source_configs["feature_cols"] ? props.source_configs["feature_cols"].join(", ") : ""}</Text>
              </Stack>
            )}
            {props.source_configs["agg_method"] && (
              <Stack
                direction={{ base: "column", md: "row" }}
                spacing={{ base: "1.5", md: "8" }}
                justifyContent="space-between"
              >
                <Text width="30%" fontWeight="bold">
                  Aggregation Method:
                </Text>
                <Text width="70%">{props.source_configs["agg_method"]}</Text>
              </Stack>
            )}
            {props.source_configs["impute_method"] && (
              <Stack
                direction={{ base: "column", md: "row" }}
                spacing={{ base: "1.5", md: "8" }}
                justifyContent="space-between"
              >
                <Text width="30%" fontWeight="bold">
                  Imputation Method:
                </Text>
                <Text width="70%">{props.source_configs["impute_method"]}</Text>
              </Stack>
            )}
          </Stack>
        </Stack>
      </Container>
      <Divider />
      <Flex direction="row-reverse" py="4" px={{ base: "4", md: "6" }}>
        <Button
          ml="2rem"
          onClick={() => props.createSource()}
          colorScheme="facebook"
          isLoading={props.isCreatingSource}
          loadingText="Creating Source"
        >
          Create source
        </Button>
        <Button onClick={() => props.goToPrevStep()} colorScheme="facebook">
          Prev
        </Button>
      </Flex>
    </Box>
  );
};

export default ConfirmCreateSource;
