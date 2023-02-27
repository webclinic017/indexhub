import React, { useEffect, useState} from "react";
import { Container, Stack } from '@chakra-ui/react'
import { useStep } from "../../utilities/hooks/useStep";
import { Step } from "../../components/step";
import SourcePath from "./steps/source_path";
import ConfigureSource from "./steps/configure_source";
import { useToast } from '@chakra-ui/react'
import Toast from "../../components/toast";
import ConfirmCreateSource from "./steps/confirm_create_source";
import { useAuth0AccessToken } from "../../utilities/hooks/auth0";
import { getSourceColumns, createSource as createSourceApi} from "../../utilities/backend_calls/source";
import { useSelector } from "react-redux";
import { AppState } from "../../index";
import { useNavigate } from "react-router-dom";


const steps = [
  {
    title: 'Step 1',
    description: 'Your source destination',
  },
  {
    title: 'Step 2',
    description: 'Configure your source',
  },
  {
    title: 'Step 3',
    description: 'Confirm source creation',
  },
]

export default function NewSource() {
  const [s3_data_bucket, setS3DataBucket] = useState("")
  const [raw_source_path, setRawSourcePath] = useState("")
  const [source_name, setSourceName] = useState("")
  const [source_columns, setSourceColumns] = useState([""])
  const [column_options, setColumnOptions] = useState([""])
  const [time_col, setTimeCol] = useState("")
  const [freq, setFreq] = useState("d")
  const [entity_cols, setEntityCols] = useState([])
  const [target_cols, setTargetCols] = useState([])
  const [manual_forecast_path, setManualForecastPath] = useState("")
  const [currentStep, { goToNextStep, goToPrevStep }] = useStep({ maxStep: steps.length })
  const access_token_indexhub_api = useAuth0AccessToken()
  
  const toast = useToast()
  const navigate = useNavigate()

  const user_details = useSelector(
    (state: AppState) => state.reducer?.user
  );

  useEffect(() => {
    setColumnOptions(source_columns)
  }, [source_columns])

  useEffect(() => {
    let selected_columns: string[] = entity_cols.concat(target_cols)
    selected_columns.push(time_col)
    selected_columns = selected_columns.filter((val) => {return val != ""})

    const optionsToRemove = new Set(selected_columns);

    const new_options = source_columns.filter((col) => {
      return !optionsToRemove.has(col);
    });
  
    setColumnOptions(new_options)
  }, [time_col, entity_cols, target_cols, manual_forecast_path])

  const submitSourcePath = async () => {
    if (raw_source_path && source_name && s3_data_bucket){
      const source_columns = await getSourceColumns(s3_data_bucket, raw_source_path, access_token_indexhub_api)
      if (Object.keys(source_columns).includes("columns")){
        setSourceColumns(source_columns["columns"])
        goToNextStep()
      } else {
        Toast(toast, "Error", source_columns["detail"], "error")
      }
    } else {
      Toast(toast, "Empty / Invalid Columns", "Please ensure all required columns are filled with valid values", "error")
    }
  }

  const submitSourceConfig = () => {
    if (time_col && freq && entity_cols && target_cols && manual_forecast_path) {
      goToNextStep()
    } else {
      Toast(toast, "Empty / Invalid Columns", "Please ensure all required columns are filled with valid values", "error")
    }
  }

  const createSource = async () => {
    
    const create_source_response = await createSourceApi(user_details.user_id, source_name, raw_source_path, freq, s3_data_bucket, time_col, entity_cols, target_cols, access_token_indexhub_api)
    if (Object.keys(create_source_response).includes("source_id")){
      Toast(toast, "Preprocessing Source", "We will let you know when it's ready to create reports", "info")
      navigate("/sources")
    } else {
      Toast(toast, "Error", create_source_response["detail"], "error")
    }
  }

  const stepScreens: Record<number, JSX.Element> = {
    0: <SourcePath setSourceName={setSourceName} setRawSourcePath={setRawSourcePath} setS3DataBucket={setS3DataBucket} submitSourcePath={submitSourcePath}/>,
    1: <ConfigureSource 
        column_options={column_options} 
        submitSourceConfig={submitSourceConfig} 
        goToPrevStep={goToPrevStep}
        setTimeCol={setTimeCol}
        setFreq={setFreq}
        setEntityCols={setEntityCols}
        setTargetCols={setTargetCols}
        setManualForecastPath={setManualForecastPath}
       />,
    2: <ConfirmCreateSource 
        createSource={createSource} 
        goToPrevStep={goToPrevStep}
        source_name={source_name}
        s3_data_bucket={s3_data_bucket}
        raw_source_path={raw_source_path}
        freq={freq}
        time_col={time_col}
        target_cols={target_cols}
        entity_cols={entity_cols}
        manual_forecast_path={manual_forecast_path}
       />
  }

  return (
      <Container maxWidth="920px" py={{ base: '8', md: '16' }}>
        <Stack direction={{ base: 'column', md: 'row' }} spacing="4" mb="3rem">
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
      </Container>
  )
}
