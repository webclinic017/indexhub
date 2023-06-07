import React, { useEffect, useState } from "react";
import {
  Container,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  Stack,
  Text,
  useDisclosure,
} from "@chakra-ui/react";
import { useStep } from "../../utilities/hooks/useStep";
import { Step } from "../../components/step";
import SourcePath from "./steps/source_path";
import ConfigureSource from "./steps/configure_source";
import { useToast } from "@chakra-ui/react";
import Toast from "../../components/toast";
import ConfirmCreateSource from "./steps/confirm_create_source";
import { useAuth0AccessToken } from "../../utilities/hooks/auth0";
import {
  createSource as createSourceApi,
  getConnectionsSchema,
  getDatasetsSchema,
  getS3SourceColumns,
} from "../../utilities/backend_calls/source";
import { useSelector } from "react-redux";
import { AppState } from "../../index";
import SourceType from "./steps/source_type";
import SourceCredentials from "./source_credentials";
import { createCredentials } from "../../utilities/backend_calls/credentials";

const steps = [
  {
    title: "Step 1",
    description: "Your source type",
  },
  {
    title: "Step 2",
    description: "Your source destination",
  },
  {
    title: "Step 3",
    description: "Configure your dataset",
  },
  {
    title: "Step 4",
    description: "Confirm source creation",
  },
];

export default function NewSource(props: {
  onCloseNewSourceModal: () => void;
}) {
  const [conn_schema, setConnectionsSchema] = useState<Record<any, any>>({});
  const [datasets_schema, setDatasetsSchema] = useState<Record<any, any>>({});

  const [source_tag, setSourceTag] = useState("");
  const [source_configs, setSourceConfigs] = useState<Record<string, any>>({});
  const [source_columns, setSourceColumns] = useState([""]);
  const [column_options, setColumnOptions] = useState([""]);
  const [currentStep, { goToNextStep, goToPrevStep }] = useStep({
    maxStep: steps.length,
  });
  const access_token_indexhub_api = useAuth0AccessToken();

  const [isLoadingSourceColumns, setIsLoadingSourceColumns] = useState(false);
  const [isCreatingSource, setIsCreatingSource] = useState(false);

  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();

  const user_details = useSelector((state: AppState) => state.reducer?.user);

  useEffect(() => {
    const getConnectionsSchemaApi = async () => {
      const conn_schema = await getConnectionsSchema(
        user_details.id,
        access_token_indexhub_api
      );
      setConnectionsSchema(conn_schema);
    };

    const getDatasetsSchemaApi = async () => {
      const datasets_schema = await getDatasetsSchema(
        access_token_indexhub_api
      );
      setDatasetsSchema(datasets_schema);
    };

    if (access_token_indexhub_api && user_details.id) {
      getConnectionsSchemaApi();
      getDatasetsSchemaApi();
    }
  }, [access_token_indexhub_api, user_details]);

  useEffect(() => {
    setColumnOptions(source_columns);
  }, [source_columns]);

  const submitSourceType = (source_tag: string) => {
    setSourceTag(source_tag);
    if (conn_schema[source_tag]["is_authenticated"]) {
      goToNextStep();
    } else {
      onOpen();
    }
  };

  const submitSourceCreds = async (source_creds: Record<string, string>) => {
    const response = await createCredentials(
      source_creds,
      source_tag,
      user_details.id,
      access_token_indexhub_api
    );
    if (Object.keys(response).includes("ok")) {
      onClose();
      Toast(
        toast,
        "Credentials Stored",
        `Credentials for your ${source_tag} source have been securely stored`,
        "success"
      );
      goToNextStep();
    } else {
      Toast(toast, "Error", response["detail"], "error");
    }
  };

  const submitSourcePath = async (configs: Record<string, string>) => {
    if (
      Object.keys(conn_schema[source_tag]["conn_fields"]).every((variable) =>
        Object.keys(configs).includes(variable)
      ) &&
      Object.keys(configs).includes("source_name")
    ) {
      setIsLoadingSourceColumns(true);
      let source_columns: Record<string, any> = [];
      if (source_tag == "s3") {
        source_columns = await getS3SourceColumns(
          configs["bucket_name"],
          configs["object_path"],
          configs["file_ext"],
          access_token_indexhub_api
        );
      }
      if (Object.keys(source_columns).includes("data")) {
        setSourceConfigs(configs);
        setSourceColumns(Object.keys(source_columns["data"]));
        goToNextStep();
      } else {
        Toast(toast, "Error", source_columns["detail"], "error");
      }
      setIsLoadingSourceColumns(false);
    } else {
      Toast(
        toast,
        "Empty / Invalid Columns",
        "Please ensure all required columns are filled with valid values",
        "error"
      );
    }
  };

  const submitSourceConfig = (
    datasetConfigs: Record<any, any>,
    datasetType: string
  ) => {
    let required_fields_filled = false;
    let concatenated_selected_columns: string[] = [];

    if (datasetType == "panel") {
      required_fields_filled =
        datasetConfigs["datetime_fmt"] &&
        datasetConfigs["entity_cols"] &&
        datasetConfigs["freq"] &&
        datasetConfigs["target_col"] &&
        datasetConfigs["time_col"];
      concatenated_selected_columns = concatenated_selected_columns.concat(
        datasetConfigs["entity_cols"],
        datasetConfigs["feature_cols"],
        [datasetConfigs["target_col"], datasetConfigs["time_col"]]
      );
    } else if (datasetType == "transaction") {
      required_fields_filled =
        datasetConfigs["datetime_fmt"] &&
        datasetConfigs["freq"] &&
        datasetConfigs["time_col"] &&
        datasetConfigs["invoice_col"] &&
        datasetConfigs["price_col"] &&
        datasetConfigs["quantity_col"] &&
        datasetConfigs["product_col"];
      concatenated_selected_columns = concatenated_selected_columns.concat(
        datasetConfigs["entity_cols"],
        datasetConfigs["feature_cols"],
        [datasetConfigs["target_col"], datasetConfigs["time_col"]],
        datasetConfigs["invoice_col"],
        datasetConfigs["price_col"],
        datasetConfigs["quantity_col"],
        datasetConfigs["product_col"]
      );
    }

    concatenated_selected_columns = concatenated_selected_columns.filter(
      (e) => e !== "" && e !== undefined
    );
    const no_duplicate_columns =
      concatenated_selected_columns.length ==
      new Set(concatenated_selected_columns).size;

    const new_source_configs = {
      ...source_configs,
      ...datasetConfigs,
      dataset_type: datasetType,
    };

    setSourceConfigs(new_source_configs);

    if (required_fields_filled && no_duplicate_columns) {
      goToNextStep();
    } else {
      Toast(
        toast,
        "Empty / Invalid Columns",
        "Please ensure all required columns are filled with valid values",
        "error"
      );
    }
  };

  const createSource = async () => {
    setIsCreatingSource(true);
    const create_source_response = await createSourceApi(
      user_details.id,
      source_tag,
      source_configs,
      access_token_indexhub_api
    );
    if (Object.keys(create_source_response).includes("source_id")) {
      Toast(
        toast,
        "Preprocessing Source",
        "We will let you know when it's ready to create reports",
        "info"
      );
      props.onCloseNewSourceModal();
    } else {
      Toast(toast, "Error", create_source_response["detail"], "error");
    }
    setIsCreatingSource(false);
  };

  const stepScreens: Record<number, JSX.Element> = {
    0: (
      <SourceType
        conn_schema={conn_schema}
        submitSourceType={submitSourceType}
      />
    ),
    1: (
      <SourcePath
        source_tag={source_tag}
        conn_schema={conn_schema}
        goToPrevStep={goToPrevStep}
        submitSourcePath={submitSourcePath}
        isLoadingSourceColumns={isLoadingSourceColumns}
      />
    ),
    2: (
      <ConfigureSource
        column_options={column_options}
        datasets_schema={datasets_schema}
        submitSourceConfig={submitSourceConfig}
        goToPrevStep={goToPrevStep}
      />
    ),
    3: (
      <ConfirmCreateSource
        source_configs={source_configs}
        source_tag={source_tag}
        createSource={createSource}
        goToPrevStep={goToPrevStep}
        isCreatingSource={isCreatingSource}
      />
    ),
  };

  return (
    <>
      <Text fontSize="2xl" fontWeight="bold" width="98%" textAlign="left">
        New data source
      </Text>
      <Container maxWidth="920px" py={{ base: "8", md: "16" }}>
        <Stack direction={{ base: "column", md: "row" }} spacing="4" mb="3rem">
          {steps.map((step, id) => (
            <Step
              key={id}
              title={step.title}
              description={step.description}
              isActive={currentStep === id}
              isCompleted={currentStep > id}
            />
          ))}
        </Stack>
        {stepScreens[currentStep]}
        <Modal isOpen={isOpen} onClose={onClose}>
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>
              <Text>Credentials</Text>
            </ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              {source_tag && (
                <SourceCredentials
                  required_credentials_schema={
                    conn_schema[source_tag]["credentials"]
                  }
                  submitSourceCreds={submitSourceCreds}
                />
              )}
            </ModalBody>
          </ModalContent>
        </Modal>
      </Container>
    </>
  );
}
