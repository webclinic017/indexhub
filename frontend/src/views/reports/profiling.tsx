import { Box, Stack, Spinner, Text } from "@chakra-ui/react"
import React, { useEffect, useState } from "react"
import { useParams } from "react-router-dom";
import { getSourceProfilingHtml } from "../../utilities/backend_calls/report";
import { useAuth0AccessToken } from "../../utilities/hooks/auth0";


const SourceProfiling = () => {
    const params = useParams();
    const access_token_indexhub_api = useAuth0AccessToken()

    const [profiling_html, setProfilingHtml] = useState("")
    
    useEffect(() => {

        const getSourceProfilingHtmlApi = async () => {
            const response:Record<string, string> = await getSourceProfilingHtml(params.source_id ? params.source_id : "", access_token_indexhub_api)
            if (Object.keys(response).includes("data")){
                setProfilingHtml(response.data)
            }
        }
        if (params.source_id) {
            getSourceProfilingHtmlApi()
        }
    }, [params.source_id])

    return (
        profiling_html ?  <Box width="100%" height="100%" as="iframe" srcDoc={profiling_html} ></Box> : <Stack alignItems="center" justifyContent="center" height="full"><Spinner/><Text>Loading...</Text></Stack>
    )
}

export default SourceProfiling